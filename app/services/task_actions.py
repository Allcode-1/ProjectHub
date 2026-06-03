from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.project import Project
from app.models.sprint import Sprint

from app.schemas.task import TaskUpdate, TaskCreate

from app.repositories.task import TaskRepository
from app.repositories.project import ProjectRepository


def add_task(
    payload: TaskCreate, project: Project, sprint: Sprint, user: User, db: Session
) -> Task:

    task_repo = TaskRepository(db)
    project_repo = ProjectRepository(db)

    if payload.worker_id:
        worker = project_repo.project_worker_by_id(project.id, payload.worker_id)
        if worker is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found"
            )

    task = task_repo.create(
        project_id=project.id,
        sprint_id=sprint.id,
        creator_id=user.id,
        worker_id=payload.worker_id,
        title=payload.title,
        description=payload.description,
    )

    db.commit()
    db.refresh(task)

    return task


def update_task(payload: TaskUpdate, task: Task, user: User, db: Session) -> Task:

    if task.creator_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Task is not yours"
        )

    updated_fields = payload.model_dump(exclude_unset=True)

    for field, value in updated_fields.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task


def delete_task(task: Task, user: User, db: Session) -> None:

    if task.creator_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Task is not yours"
        )

    db.delete(task)
    db.commit()

    return None


def take_task_to_work(task: Task, user: User, db: Session) -> Task:

    if task.worker_id is not None or task.status != TaskStatus.TODO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task is already taken"
        )

    task.worker_id = user.id
    task.status = TaskStatus.IN_PROGRESS

    db.commit()
    db.refresh(task)

    return task


def send_task_to_review(task: Task, user: User, db: Session) -> Task:

    if task.worker_id != user.id or task.status != TaskStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Can't send task to review"
        )

    task.status = TaskStatus.REVIEW

    db.commit()
    db.refresh(task)

    return task


def accept_task_review(task: Task, user: User, db: Session) -> Task:

    if task.worker_id == user.id or task.status != TaskStatus.REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task need to be on review"
        )

    task.status = TaskStatus.DONE

    db.commit()
    db.refresh(task)

    return task


def decline_task_review(task: Task, user: User, db: Session) -> Task:

    if task.worker_id == user.id or task.status != TaskStatus.REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task need to be on review"
        )

    task.status = TaskStatus.REJECTED

    db.commit()
    db.refresh(task)

    return task


def renew_task(task: Task, user: User, db: Session) -> Task:

    if task.status != TaskStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task need to be rejected"
        )

    task.status = TaskStatus.TODO

    db.commit()
    db.refresh(task)

    return task
