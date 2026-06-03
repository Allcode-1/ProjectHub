from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.dependencies import get_current_active_user

from app.models.user import User
from app.models.project import Project

from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.auth.schemas import UserRead

from app.services.project_actions import create_project, update_project, delete_project

from app.repositories.project import ProjectRepository

from app.dependencies.project import (
    require_can_manage_sprints,
    require_can_view_project,
)


router = APIRouter()


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def add_project_router(
    payload: ProjectCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return create_project(payload, user, db)


@router.get("/", response_model=list[ProjectRead])
def get_projects_router(
    user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):

    project_repo = ProjectRepository(db)
    return project_repo.list_accessible_by_user(user.id)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project_router(
    project: Project = Depends(require_can_view_project),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_router(
    project: Project = Depends(require_can_manage_sprints),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return delete_project(project, user, db)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project_router(
    payload: ProjectUpdate,
    project: Project = Depends(require_can_manage_sprints),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return update_project(payload, project, user, db)


@router.get("/{project_id}/members", response_model=list[UserRead])
def get_project_members(
    project: Project = Depends(require_can_view_project),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project_repo = ProjectRepository(db)
    project_members = project_repo.list_project_members(project.id)

    return project_members
