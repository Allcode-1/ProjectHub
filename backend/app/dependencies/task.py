from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.dependencies.sprint import get_sprint_by_id_or_404
from backend.app.models.sprint import Sprint
from backend.app.repositories.task import TaskRepository

DbSession = Annotated[Session, Depends(get_db)]
CurrentSprint = Annotated[Sprint, Depends(get_sprint_by_id_or_404)]


def get_task_by_id_or_404(
    task_id: int,
    sprint: CurrentSprint,
    db: DbSession,
):

    task_repo = TaskRepository(db)

    task = task_repo.task_by_id(sprint.project_id, sprint.id, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    return task
