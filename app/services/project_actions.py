from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.project import Project

from app.schemas.project import ProjectCreate, ProjectUpdate

from app.repositories.project import ProjectRepository


def create_project(payload: ProjectCreate, user: User, db: Session) -> Project:

    project_repo = ProjectRepository(db)

    project = project_repo.create(
        owner_id=user.id, name=payload.name, description=payload.description
    )

    db.commit()
    db.refresh(project)

    return project


def update_project(
    payload: ProjectUpdate, project: Project, user: User, db: Session
) -> Project:

    if project.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    updated_fields = payload.model_dump(exclude_unset=True)

    for field, value in updated_fields.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return project


def delete_project(project: Project, user: User, db: Session) -> None:

    if project.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    db.delete(project)
    db.commit()

    return None
