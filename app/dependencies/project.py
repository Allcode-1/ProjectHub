from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.project import ProjectRepository


def get_project_by_id_or_404(project_id: int, db: Session = Depends(get_db)):

    project_repo = ProjectRepository(db)

    project = project_repo.get_by_id(project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    return project
