from typing import Annotated

from fastapi import Depends
from redis import Redis

from backend.app.redis.client import get_redis
from backend.app.cache.base import RedisCache
from backend.app.cache.project import ProjectCache
from backend.app.cache.sprint import SprintCache

RedisDep = Annotated[Redis, Depends(get_redis)]


def get_cache(redis: RedisDep) -> RedisCache:
    return RedisCache(redis)


RedisCacheDep = Annotated[RedisCache, Depends(get_cache)]


def get_project_cache(cache: RedisCacheDep) -> ProjectCache:
    return ProjectCache(cache)


def get_sprint_cache(cache: RedisCacheDep) -> SprintCache:
    return SprintCache(cache)
