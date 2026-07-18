from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent.parent.parent


class Auth_JWT(BaseModel):
    public_key_path: Path = BASE_DIR / "certs" / "public.pem"
    private_key_path: Path = BASE_DIR / "certs" / "private.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    app_name: str = "ProjectHub"
    log_level: str = "INFO"
    healthcheck_timeout_seconds: float = 1.0
    readiness_require_redis: bool = True
    readiness_require_rabbitmq: bool = False

    auth_jwt: Auth_JWT = Auth_JWT()
    redis_url: str = "redis://localhost:6390/0"

    celery_broker_url: str = "amqp://guest:guest@localhost:5672//"


settings = Settings()
