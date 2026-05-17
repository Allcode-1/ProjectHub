from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.dependencies import get_current_active_user
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.user import User

from app.schemas.sprint import SprintCreate, SprintRead, SprintUpdate

from app.services.project_membership import (
    can_view_project,
    can_manage_sprints,
)


router = APIRouter()


@router.post("/", response_model=SprintRead, status_code=status.HTTP_201_CREATED)
def add_sprint(
    project_id: int,
    payload: SprintCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project = db.scalar(
        select(Project).where(Project.id == project_id)
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    sprint = Sprint(
        project_id=project_id,
        creator_id=user.id,
        name=payload.name,
        description=payload.description,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
    )

    db.add(sprint)
    db.commit()
    db.refresh(sprint)

    return sprint


@router.get("/", response_model=list[SprintRead])
def get_sprints(
    project_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project = db.scalar(select(Project).where(Project.id == project_id))

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_view_project(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    sprints = db.scalars(
        select(Sprint).where(
            Sprint.project_id == project_id
        )
    ).all()

    return sprints


@router.get("/{sprint_id}", response_model=SprintRead)
def get_sprint(
    project_id: int,
    sprint_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project = db.scalar(select(Project).where(Project.id == project_id))

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_view_project(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    sprint = db.scalar(
        select(Sprint).where(
            Sprint.project_id == project_id,
            Sprint.id == sprint_id,
        )
    )

    if sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found"
        )

    return sprint


@router.delete("/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sprint(
    project_id: int,
    sprint_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project = db.scalar(select(Project).where(Project.id == project_id))

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found"
        )

    sprint = db.scalar(
        select(Sprint).where(
            Sprint.project_id == project_id,
            Sprint.id == sprint_id,
        )
    )

    if sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found"
        )

    db.delete(sprint)
    db.commit()

    return None


@router.patch("/{sprint_id}", response_model=SprintRead)
def update_sprint(
    project_id: int,
    sprint_id: int,
    payload: SprintUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project = db.scalar(select(Project).where(Project.id == project_id))

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    sprint = db.scalar(
        select(Sprint).where(
            Sprint.project_id == project_id,
            Sprint.id == sprint_id,
        )
    )

    if sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found"
        )

    updated_fields = payload.model_dump(exclude_unset=True)
    for field, value in updated_fields.items():
        setattr(sprint, field, value)

    db.commit()
    db.refresh(sprint)

    return sprint
