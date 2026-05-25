from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.dependencies import get_current_active_user
from app.models.sprint import SprintStatus
from app.models.user import User
from app.models.project import Project
from app.models.sprint import Sprint

from app.schemas.sprint import SprintCreate, SprintRead, SprintUpdate

from app.services.project_membership import (
    can_view_project,
    can_manage_sprints,
)

from app.repositories.sprint import SprintRepository

from app.dependencies.project import get_project_by_id_or_404
from app.dependencies.sprint import get_sprint_by_id_or_404


router = APIRouter()


@router.post("/", response_model=SprintRead, status_code=status.HTTP_201_CREATED)
def add_sprint(
    payload: SprintCreate,
    project: Project = Depends(get_project_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    sprint_repo = SprintRepository(db)

    starts_at = payload.starts_at or datetime.now(timezone.utc)
    ends_at = starts_at + timedelta(days=14)

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    sprint = sprint_repo.create(
        project_id=project.id,
        creator_id=user.id,
        name=payload.name,
        description=payload.description,
        starts_at=starts_at,
        ends_at=ends_at,
    )

    db.commit()
    db.refresh(sprint)

    return sprint


@router.get("/", response_model=list[SprintRead])
def get_sprints(
    project: Project = Depends(get_project_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    sprint_repo = SprintRepository(db)

    if not can_view_project(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    sprints = sprint_repo.all_sprints(project.id)

    return sprints


@router.get("/{sprint_id}", response_model=SprintRead)
def get_sprint(
    project: Project = Depends(get_project_by_id_or_404),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    if not can_view_project(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    return sprint


@router.delete("/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sprint(
    project: Project = Depends(get_project_by_id_or_404),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found"
        )

    db.delete(sprint)
    db.commit()

    return None


@router.patch("/{sprint_id}", response_model=SprintRead)
def update_sprint(
    payload: SprintUpdate,
    project: Project = Depends(get_project_by_id_or_404),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found"
        )

    updated_fields = payload.model_dump(exclude_unset=True)
    for field, value in updated_fields.items():
        setattr(sprint, field, value)

    db.commit()
    db.refresh(sprint)

    return sprint


@router.patch("/{sprint_id}/start", response_model=SprintRead)
def start_sprint_before_time(
    project: Project = Depends(get_project_by_id_or_404),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found"
        )

    now = datetime.now(timezone.utc)

    if now > sprint.starts_at:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Sprint already started"
        )

    sprint.starts_at = now
    sprint.status = SprintStatus.ACTIVE

    db.commit()
    db.refresh(sprint)

    return sprint


@router.patch("/{sprint_id}/close", response_model=SprintRead)
def close_sprint_before_time(
    project: Project = Depends(get_project_by_id_or_404),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found"
        )

    now = datetime.now(timezone.utc)

    sprint.closed_at = now

    db.commit()
    db.refresh(sprint)

    return sprint
