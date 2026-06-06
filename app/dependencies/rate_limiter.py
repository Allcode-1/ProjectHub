from fastapi import Depends
from redis import Redis

from app.redis.client import get_redis
from app.services.rate_limiter import RateLimiter


def get_rate_limiter(redis: Redis = Depends(get_redis)) -> RateLimiter:
    return RateLimiter(redis)
