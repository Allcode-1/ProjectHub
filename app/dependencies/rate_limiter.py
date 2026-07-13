from typing import Annotated

from fastapi import Depends
from redis import Redis

from app.redis.client import get_redis
from app.security.rate_limiter import RateLimiter

RedisDep = Annotated[Redis, Depends(get_redis)]


def get_rate_limiter(redis: RedisDep) -> RateLimiter:
    return RateLimiter(redis)
