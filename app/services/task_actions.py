from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.project import Project
from app.models.sprint import Sprint

from app.schemas.task import TaskUpdate, TaskCreate
from app.schemas.review_comments import ReviewCommentCreate

from app.repositories.task import TaskRepository
from app.repositories.project import ProjectRepository
from app.repositories.review_comment import ReviewCommentRepository

from app.services.project_membership import can_manage_sprints


def add_task(
    payload: TaskCreate, project: Project, sprint: Sprint, user: User, db: Session
) -> Task:

    task_repo = TaskRepository(db)
    project_repo = ProjectRepository(db)

    if payload.worker_id is not None:
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

    task.status = TaskStatus.TODO

    db.commit()
    db.refresh(task)

    return task


def update_task(
    payload: TaskUpdate,
    project: Project,
    task: Task,
    user: User,
    db: Session,
) -> Task:

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    updated_fields = payload.model_dump(exclude_unset=True)

    worker_id = updated_fields.get("worker_id")
    if worker_id is not None:
        project_repo = ProjectRepository(db)
        worker = project_repo.project_worker_by_id(project.id, worker_id)
        if worker is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found"
            )

    for field, value in updated_fields.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task


def delete_task(project: Project, task: Task, user: User, db: Session) -> None:

    if not can_manage_sprints(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    db.delete(task)
    db.commit()

    return None


def take_task_to_work(task: Task, user: User, db: Session) -> Task:

    if task.status != TaskStatus.TODO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task is not available"
        )

    if task.worker_id is not None and task.worker_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is assigned to another worker",
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


def decline_task_review(
    payload: ReviewCommentCreate | None,
    task: Task,
    user: User,
    db: Session,
) -> Task:

    if task.worker_id == user.id or task.status != TaskStatus.REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task need to be on review"
        )

    if payload is not None and payload.comment is not None:
        review_comment_repo = ReviewCommentRepository(db)
        review_comment_repo.create(
            task_id=task.id,
            comment=payload.comment,
            author_id=user.id,
        )

    task.status = TaskStatus.REJECTED

    db.commit()
    db.refresh(task)

    return task


def renew_task(task: Task, user: User, db: Session) -> Task:

    if task.worker_id != user.id or task.status != TaskStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Can't renew task",
        )

    task.status = TaskStatus.IN_PROGRESS

    db.commit()
    db.refresh(task)

    return task
