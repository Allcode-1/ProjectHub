from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.dependencies.cache import get_project_cache
from backend.app.repositories.project import ProjectRepository
from backend.app.cache.project import ProjectCache
from backend.app.services.project_queries import ProjectQueryService

DbSession = Annotated[Session, Depends(get_db)]
ProjectCacheDep = Annotated[ProjectCache, Depends(get_project_cache)]


def get_project_query_service(
    db: DbSession,
    project_cache: ProjectCacheDep,
) -> ProjectQueryService:

    return ProjectQueryService(
        project_repo=ProjectRepository(db), project_cache=project_cache
    )
