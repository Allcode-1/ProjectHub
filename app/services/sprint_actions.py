from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.project import Project
from app.models.sprint import Sprint, SprintStatus

from app.schemas.sprint import SprintCreate, SprintUpdate

from app.repositories.sprint import SprintRepository

from app.services.project_membership import can_manage_sprints


def create_sprint(
    payload: SprintCreate, project: Project, user: User, db: Session
) -> Sprint:

    sprint_repo = SprintRepository(db)

    starts_at = payload.starts_at or datetime.now(timezone.utc)
    ends_at = starts_at + timedelta(days=14)

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


def update_sprint(
    payload: SprintUpdate, project: Project, sprint: Sprint, user: User, db: Session
) -> Sprint:

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    updated_fields = payload.model_dump(exclude_unset=True)
    for field, value in updated_fields.items():
        setattr(sprint, field, value)

    db.commit()
    db.refresh(sprint)

    return sprint


def delete_sprint(project: Project, sprint: Sprint, user: User, db: Session) -> None:

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    db.delete(sprint)
    db.commit()

    return None


def start_sprint(project: Project, sprint: Sprint, user: User, db: Session) -> Sprint:

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
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


def close_sprint(project: Project, sprint: Sprint, user: User, db: Session) -> Sprint:

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    now = datetime.now(timezone.utc)

    sprint.closed_at = now
    sprint.status = SprintStatus.CLOSED

    db.commit()
    db.refresh(sprint)

    return sprint
