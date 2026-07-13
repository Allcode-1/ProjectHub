from datetime import datetime, timezone

from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import utils as auth_utils
from app.auth.schemas import TokenPair, UserCreate
from app.auth.tokens import create_access_token, create_refresh_token
from app.core.errors import AppError
from app.models.refresh_session import RefreshSession
from app.models.user import User


def _invalid_token_error() -> AppError:
    return AppError(401, "Invalid token")


def _decode_refresh_payload(refresh_token: str) -> dict:
    try:
        token_payload = auth_utils.decode_jwt(token=refresh_token)
    except InvalidTokenError as exc:
        raise _invalid_token_error() from exc

    if token_payload.get("type") != "refresh":
        raise _invalid_token_error()

    if token_payload.get("jti") is None:
        raise _invalid_token_error()

    return token_payload


def _get_refresh_session(db: Session, jti: str) -> RefreshSession:
    refresh_session = db.scalar(select(RefreshSession).where(RefreshSession.jti == jti))

    if not refresh_session:
        raise _invalid_token_error()

    return refresh_session


def _create_token_pair(user: User, db: Session) -> TokenPair:
    access_token = create_access_token(user)
    refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(user)

    refresh_session = RefreshSession(
        jti=refresh_jti,
        user_id=user.id,
        expires_at=refresh_expires_at,
    )

    db.add(refresh_session)
    db.commit()

    return TokenPair(access_token=access_token, refresh_token=refresh_token)


def register_user(payload: UserCreate, db: Session) -> User:
    existing_user = db.scalar(select(User).where(User.username == payload.username))

    if existing_user:
        raise AppError(409, "Username or email are already taken")

    existing_email = db.scalar(select(User).where(User.email == payload.email))

    if existing_email:
        raise AppError(409, "Username or email are already taken")

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=auth_utils.hash_password(payload.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(username: str, password: str, db: Session) -> User:
    user = db.scalar(select(User).where(User.username == username))

    if not user:
        raise AppError(401, "Profile not found")

    if not auth_utils.validate_password(password, user.hashed_password):
        raise AppError(401, "Invalid credentials")

    if not user.is_active:
        raise AppError(403, "User inactive")

    return user


def login_user(username: str, password: str, db: Session) -> TokenPair:
    user = authenticate_user(username, password, db)
    return _create_token_pair(user, db)


def logout_user(refresh_token: str, db: Session) -> dict[str, str]:
    token_payload = _decode_refresh_payload(refresh_token)
    refresh_session = _get_refresh_session(db, token_payload["jti"])

    refresh_session.revoked_at = datetime.now(timezone.utc)

    db.commit()
    return {"message": "Logged out"}


def refresh_tokens(refresh_token: str, db: Session) -> TokenPair:
    token_payload = _decode_refresh_payload(refresh_token)
    refresh_session = _get_refresh_session(db, token_payload["jti"])

    if refresh_session.revoked_at is not None:
        raise _invalid_token_error()

    now = datetime.now(timezone.utc)

    if refresh_session.expires_at < now:
        raise _invalid_token_error()

    user_id = token_payload.get("sub")

    if user_id is None:
        raise _invalid_token_error()

    try:
        user = db.get(User, int(user_id))
    except (TypeError, ValueError) as exc:
        raise _invalid_token_error() from exc

    if not user or not user.is_active:
        raise _invalid_token_error()

    refresh_session.revoked_at = now

    return _create_token_pair(user, db)
