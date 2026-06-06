from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.cache import get_project_cache
from app.repositories.project import ProjectRepository
from app.cache.project import ProjectCache
from app.services.project_queries import ProjectQueryService


def get_project_query_service(
    db: Session = Depends(get_db),
    project_cache: ProjectCache = Depends(get_project_cache),
) -> ProjectQueryService:

    return ProjectQueryService(
        project_repo=ProjectRepository(db), project_cache=project_cache
    )
