from dataclasses import dataclass
from typing import Annotated

from fastapi import Query

from app.core.config import settings


@dataclass(frozen=True)
class Pagination:
    limit: int
    offset: int


def get_pagination(
    limit: Annotated[
        int,
        Query(ge=1, le=settings.pagination.max_limit),
    ] = settings.pagination.default_limit,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Pagination:
    return Pagination(limit=limit, offset=offset)
