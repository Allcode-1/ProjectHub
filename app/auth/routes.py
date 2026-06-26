from fastapi import APIRouter, Depends, status, Form, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth import service as auth_service

from app.models.user import User

from app.auth.dependencies import get_current_active_user, require_admin

from app.auth.schemas import UserCreate, UserRead, TokenPair, RefreshToken

from app.services.rate_limiter import RateLimiter
from app.dependencies.rate_limiter import get_rate_limiter


router = APIRouter(prefix="/auth", tags=["jwt-based auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    return auth_service.register_user(payload, db)


@router.post("/login", response_model=TokenPair)
def login_user(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
):

    client_ip = request.client.host if request.client else "unknown"

    rate_limiter.check(
        key=f"rate:auth:login:ip:{client_ip}", limit=10, window_seconds=60
    )

    rate_limiter.check(
        key=f"rate:auth:login:username:{username}", limit=5, window_seconds=300
    )

    return auth_service.login_user(username, password, db)


@router.post("/logout")
def logout_user(payload: RefreshToken, db: Session = Depends(get_db)):
    return auth_service.logout_user(payload.refresh_token, db)


@router.get("/users/me", response_model=UserRead)
def get_me(
    user: User = Depends(get_current_active_user),
):

    return user


@router.get("/users", response_model=list[UserRead])
def get_all_users(user: User = Depends(require_admin), db: Session = Depends(get_db)):

    users = db.scalars(select(User).order_by(User.id)).all()

    return users


@router.post("/refresh", response_model=TokenPair)
def refresh_tokens(payload: RefreshToken, db: Session = Depends(get_db)):
    return auth_service.refresh_tokens(payload.refresh_token, db)
