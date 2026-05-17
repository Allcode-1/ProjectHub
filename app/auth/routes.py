from jwt.exceptions import InvalidTokenError
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth import utils as auth_utils

from app.models.user import User
from app.models.refresh_session import RefreshSession

from app.auth.dependencies import get_current_active_user, require_admin
from app.auth.tokens import create_access_token, create_refresh_token

from app.auth.schemas import UserCreate, UserRead, TokenPair, RefreshToken


router = APIRouter(prefix="/auth", tags=["jwt-based auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.scalar(select(User).where(User.username == payload.username))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email are already taken",
        )

    if payload.email is not None:
        existing_email = db.scalar(select(User).where(User.email == payload.email))

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email are already taken",
            )

    hashed_password = auth_utils.hash_password(payload.password)

    user = User(
        username=payload.username, email=payload.email, hashed_password=hashed_password
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenPair)
def login_user(
    username: str = Form(), password: str = Form(), db: Session = Depends(get_db)
):

    user = db.scalar(select(User).where(User.username == username))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not auth_utils.validate_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User inactive"
        )

    access_token = create_access_token(user)
    refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(user)

    refresh_session = RefreshSession(
        jti=refresh_jti, user_id=user.id, expires_at=refresh_expires_at
    )

    db.add(refresh_session)
    db.commit()

    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
def logout_user(payload: RefreshToken, db: Session = Depends(get_db)):

    refresh_token = payload.refresh_token

    try:
        token_payload = auth_utils.decode_jwt(token=refresh_token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    if token_payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    jti = token_payload.get("jti")

    if jti is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    refresh_session = db.scalar(select(RefreshSession).where(RefreshSession.jti == jti))

    if not refresh_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    refresh_session.revoked_at = datetime.now(timezone.utc)

    db.commit()
    return {"message": "Logged out"}


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

    refresh_token = payload.refresh_token

    try:
        token_payload = auth_utils.decode_jwt(token=refresh_token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    if token_payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    jti = token_payload.get("jti")

    if jti is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    refresh_session = db.scalar(select(RefreshSession).where(RefreshSession.jti == jti))

    if not refresh_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    if refresh_session.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    now = datetime.now(timezone.utc)

    if refresh_session.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user_id = token_payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    try:
        user = db.get(User, int(user_id))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    refresh_session.revoked_at = now

    new_access_token = create_access_token(user)
    new_refresh_token, new_refresh_jti, new_refresh_expire_at = create_refresh_token(
        user
    )

    new_refresh_session = RefreshSession(
        jti=new_refresh_jti, user_id=user.id, expires_at=new_refresh_expire_at
    )

    db.add(new_refresh_session)
    db.commit()

    return TokenPair(access_token=new_access_token, refresh_token=new_refresh_token)
