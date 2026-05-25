from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        project_id: int,
        sprint_id: int,
        creator_id: int,
        worker_id: int | None,
        title: str,
        description: str,
    ):

        task = Task(
            project_id=project_id,
            sprint_id=sprint_id,
            creator_id=creator_id,
            worker_id=worker_id,
            title=title,
            description=description,
        )

        self.db.add(task)
        return task

    def task_by_id(self, project_id, sprint_id, task_id) -> Task:

        return self.db.scalar(
            select(Task).where(
                Task.project_id == project_id,
                Task.sprint_id == sprint_id,
                Task.id == task_id,
            )
        )

    def all_tasks_of_sprint(self, project_id, sprint_id) -> list[Task]:

        return self.db.scalars(
            select(Task)
            .where(Task.project_id == project_id, Task.sprint_id == sprint_id)
            .order_by(Task.id)
        ).all()
