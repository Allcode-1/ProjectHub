from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.models.project import Project

from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.auth.schemas import UserRead

from app.services.project_membership import can_view_project, can_manage_sprints

from app.repositories.project import ProjectRepository

from app.dependencies.project import get_project_by_id_or_404


router = APIRouter()


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def add_project(
    payload: ProjectCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project_repo = ProjectRepository(db)

    project = project_repo.create(
        owner_id=user.id, name=payload.name, description=payload.description
    )

    db.commit()
    db.refresh(project)

    return project


@router.get("/", response_model=list[ProjectRead])
def get_projects(
    user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):

    project_repo = ProjectRepository(db)

    return project_repo.list_accessible_by_user(user.id)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project: Project = Depends(get_project_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    if not can_view_project(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project: Project = Depends(get_project_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Can not delete project"
        )

    db.delete(project)
    db.commit()

    return None


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    payload: ProjectUpdate,
    project: Project = Depends(get_project_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Can not delete project"
        )

    updated_fields = payload.model_dump(exclude_unset=True)

    for field, value in updated_fields.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return project


@router.get("/{project_id}/members", response_model=list[UserRead])
def get_project_members(
    project: Project = Depends(get_project_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project_repo = ProjectRepository(db)

    if not can_view_project(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    project_members = project_repo.list_project_members(project.id)

    return project_members
