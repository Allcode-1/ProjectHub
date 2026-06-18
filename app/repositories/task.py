from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus


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
        description: str | None,
    ) -> Task:

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

    def task_by_id(self, project_id: int, sprint_id: int, task_id: int) -> Task | None:

        return self.db.scalar(
            select(Task).where(
                Task.project_id == project_id,
                Task.sprint_id == sprint_id,
                Task.id == task_id,
            )
        )

    def all_tasks_of_sprint(self, project_id: int, sprint_id: int) -> list[Task]:

        return list(
            self.db.scalars(
                select(Task)
                .where(Task.project_id == project_id, Task.sprint_id == sprint_id)
                .order_by(Task.id)
            ).all()
        )

    def tasks_todo(self, project_id: int, sprint_id: int) -> list[Task]:

        return list(
            self.db.scalars(
                select(Task)
                .where(
                    Task.project_id == project_id,
                    Task.sprint_id == sprint_id,
                    Task.status == TaskStatus.TODO,
                )
                .order_by(Task.id)
            ).all()
        )

    def tasks_in_progress(self, project_id: int, sprint_id: int) -> list[Task]:

        return list(
            self.db.scalars(
                select(Task)
                .where(
                    Task.project_id == project_id,
                    Task.sprint_id == sprint_id,
                    Task.status == TaskStatus.IN_PROGRESS,
                )
                .order_by(Task.id)
            ).all()
        )

    def tasks_on_review(self, project_id: int, sprint_id: int) -> list[Task]:

        return list(
            self.db.scalars(
                select(Task)
                .where(
                    Task.project_id == project_id,
                    Task.sprint_id == sprint_id,
                    Task.status == TaskStatus.REVIEW,
                )
                .order_by(Task.id)
            ).all()
        )

    def tasks_rejected(self, project_id: int, sprint_id: int) -> list[Task]:

        return list(
            self.db.scalars(
                select(Task)
                .where(
                    Task.project_id == project_id,
                    Task.sprint_id == sprint_id,
                    Task.status == TaskStatus.REJECTED,
                )
                .order_by(Task.id)
            ).all()
        )

    def tasks_done(self, project_id: int, sprint_id: int) -> list[Task]:

        return list(
            self.db.scalars(
                select(Task)
                .where(
                    Task.project_id == project_id,
                    Task.sprint_id == sprint_id,
                    Task.status == TaskStatus.DONE,
                )
                .order_by(Task.id)
            ).all()
        )
