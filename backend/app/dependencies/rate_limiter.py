from typing import Annotated

from fastapi import Depends, Request
from redis import Redis

from app.auth.dependencies import get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.redis.client import get_redis
from app.security.rate_limiter import RateLimiter

RedisDep = Annotated[Redis, Depends(get_redis)]
CurrentUser = Annotated[User, Depends(get_current_active_user)]


def get_rate_limiter(redis: RedisDep) -> RateLimiter:
    return RateLimiter(redis)


RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _check_ip_rate_limit(
    prefix: str,
    request: Request,
    rate_limiter: RateLimiter,
    limit: int,
    window_seconds: int,
) -> None:
    rate_limiter.check(
        key=f"rate:{prefix}:ip:{_client_ip(request)}",
        limit=limit,
        window_seconds=window_seconds,
    )


def rate_limit_auth_register(
    request: Request,
    rate_limiter: RateLimiterDep,
) -> None:
    _check_ip_rate_limit(
        "auth:register",
        request,
        rate_limiter,
        settings.rate_limit.register_ip_limit,
        settings.rate_limit.register_ip_window_seconds,
    )


def rate_limit_auth_refresh(
    request: Request,
    rate_limiter: RateLimiterDep,
) -> None:
    _check_ip_rate_limit(
        "auth:refresh",
        request,
        rate_limiter,
        settings.rate_limit.refresh_ip_limit,
        settings.rate_limit.refresh_ip_window_seconds,
    )


def rate_limit_auth_logout(
    request: Request,
    rate_limiter: RateLimiterDep,
) -> None:
    _check_ip_rate_limit(
        "auth:logout",
        request,
        rate_limiter,
        settings.rate_limit.logout_ip_limit,
        settings.rate_limit.logout_ip_window_seconds,
    )


def rate_limit_authenticated_mutation(
    request: Request,
    user: CurrentUser,
    rate_limiter: RateLimiterDep,
) -> None:
    rate_limiter.check(
        key=f"rate:api:mutation:user:{user.id}",
        limit=settings.rate_limit.authenticated_mutation_user_limit,
        window_seconds=settings.rate_limit.authenticated_mutation_user_window_seconds,
    )
    rate_limiter.check(
        key=f"rate:api:mutation:ip:{_client_ip(request)}",
        limit=settings.rate_limit.authenticated_mutation_ip_limit,
        window_seconds=settings.rate_limit.authenticated_mutation_ip_window_seconds,
    )
