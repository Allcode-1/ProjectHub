from fastapi import Depends
from redis import Redis

from app.redis.client import get_redis
from app.cache.base import RedisCache
from app.cache.project import ProjectCache
from app.cache.sprint import SprintCache


def get_cache(redis: Redis = Depends(get_redis)) -> RedisCache:
    return RedisCache(redis)


def get_project_cache(cache: RedisCache = Depends(get_cache)) -> ProjectCache:
    return ProjectCache(cache)


def get_sprint_cache(cache: RedisCache = Depends(get_cache)) -> SprintCache:
    return SprintCache(cache)
