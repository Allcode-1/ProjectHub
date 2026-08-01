from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.app.core.config import settings

DATABASE_URL = settings.database_url
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")


class Base(DeclarativeBase):
    pass


def _connect_args(database_url: str) -> dict[str, object]:
    url = make_url(database_url)

    if not url.drivername.startswith("postgresql"):
        return {}

    return {
        "connect_timeout": settings.database.connect_timeout_seconds,
        "options": f"-c statement_timeout={settings.database.statement_timeout_ms}",
    }


engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout_seconds,
    pool_recycle=settings.database.pool_recycle_seconds,
    pool_pre_ping=settings.database.pool_pre_ping,
    pool_use_lifo=settings.database.pool_use_lifo,
    pool_reset_on_return="rollback",
    connect_args=_connect_args(DATABASE_URL),
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
