from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.dependencies import get_current_active_user

from app.models.user import User
from app.models.project import Project

from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.auth.schemas import UserRead

from app.services.project_actions import create_project, update_project, delete_project
from app.services.project_members import leave_project
from app.services.project_queries import ProjectQueryService

from app.repositories.project import ProjectRepository

from app.dependencies.project import (
    require_can_manage_sprints,
    require_can_view_project,
)
from app.dependencies.project_queries import get_project_query_service

from app.cache.project import ProjectCache
from app.dependencies.cache import get_project_cache

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_active_user)]
ViewProject = Annotated[Project, Depends(require_can_view_project)]
ManageSprintsProject = Annotated[Project, Depends(require_can_manage_sprints)]
ProjectCacheDep = Annotated[ProjectCache, Depends(get_project_cache)]
ProjectQueries = Annotated[ProjectQueryService, Depends(get_project_query_service)]


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def add_project_router(
    payload: ProjectCreate,
    user: CurrentUser,
    db: DbSession,
    project_cache: ProjectCacheDep,
):

    return create_project(payload, user, db, project_cache)


@router.get("/", response_model=list[ProjectRead])
def get_projects_router(
    user: CurrentUser,
    project_queries: ProjectQueries,
):

    return project_queries.list_accessible_by_user(user.id)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project_router(
    project: ViewProject,
    user: CurrentUser,
    db: DbSession,
):

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_router(
    project: ManageSprintsProject,
    user: CurrentUser,
    db: DbSession,
    project_cache: ProjectCacheDep,
):

    return delete_project(project, user, db, project_cache)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project_router(
    payload: ProjectUpdate,
    project: ManageSprintsProject,
    user: CurrentUser,
    db: DbSession,
    project_cache: ProjectCacheDep,
):

    return update_project(payload, project, user, db, project_cache)


@router.get("/{project_id}/members", response_model=list[UserRead])
def get_project_members(
    project: ViewProject,
    user: CurrentUser,
    db: DbSession,
):

    project_repo = ProjectRepository(db)
    project_members = project_repo.list_project_members(project.id)

    return project_members


@router.delete("/{project_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
def leave_project_router(
    project: ViewProject,
    user: CurrentUser,
    db: DbSession,
    project_cache: ProjectCacheDep,
):
    return leave_project(project, user, db, project_cache)
