from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.dependencies.cache import get_sprint_cache
from backend.app.repositories.sprint import SprintRepository
from backend.app.cache.sprint import SprintCache
from backend.app.services.sprint_queries import SprintQueryService

DbSession = Annotated[Session, Depends(get_db)]
SprintCacheDep = Annotated[SprintCache, Depends(get_sprint_cache)]


def get_sprint_query_service(
    db: DbSession,
    sprint_cache: SprintCacheDep,
) -> SprintQueryService:

    return SprintQueryService(
        sprint_repo=SprintRepository(db), sprint_cache=sprint_cache
    )
