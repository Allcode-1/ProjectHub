from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db

from app.dependencies.project import get_project_by_id_or_404
from app.repositories.sprint import SprintRepository
from app.models.project import Project


def get_sprint_by_id_or_404(
    sprint_id: int,
    project: Project = Depends(get_project_by_id_or_404),
    db: Session = Depends(get_db),
):

    sprint_repo = SprintRepository(db)

    sprint = sprint_repo.get_by_id(project.id, sprint_id)

    if sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found"
        )

    return sprint
