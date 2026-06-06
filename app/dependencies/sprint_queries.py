from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.cache import get_sprint_cache
from app.repositories.sprint import SprintRepository
from app.cache.sprint import SprintCache
from app.services.sprint_queries import SprintQueryService


def get_sprint_query_service(
    db: Session = Depends(get_db), sprint_cache: SprintCache = Depends(get_sprint_cache)
) -> SprintQueryService:

    return SprintQueryService(
        sprint_repo=SprintRepository(db), sprint_cache=sprint_cache
    )
