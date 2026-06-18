from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db.session import get_db
from app.dependencies.project import require_can_manage_sprints, require_can_take_tasks
from app.dependencies.sprint import get_sprint_by_id_or_404
from app.dependencies.task import get_task_by_id_or_404
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.task import Task
from app.models.user import User
from app.schemas.review_comments import ReviewCommentCreate
from app.schemas.task import TaskRead
from app.services.task_actions import (
    accept_task_review,
    decline_task_review,
    renew_task,
    send_task_to_review,
    take_task_to_work,
)


router = APIRouter()


@router.patch("/{task_id}/take_task", response_model=TaskRead)
def take_task_to_work_router(
    project: Project = Depends(require_can_take_tasks),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    task: Task = Depends(get_task_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return take_task_to_work(task, user, db)


@router.patch("/{task_id}/to_review", response_model=TaskRead)
def send_task_to_review_router(
    project: Project = Depends(require_can_take_tasks),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    task: Task = Depends(get_task_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return send_task_to_review(task, user, db)


@router.patch("/{task_id}/accept", response_model=TaskRead)
def accept_task_review_router(
    project: Project = Depends(require_can_manage_sprints),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    task: Task = Depends(get_task_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return accept_task_review(task, user, db)


@router.patch("/{task_id}/decline", response_model=TaskRead)
def decline_task_review_router(
    payload: ReviewCommentCreate | None = None,
    project: Project = Depends(require_can_manage_sprints),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    task: Task = Depends(get_task_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return decline_task_review(payload, task, user, db)


@router.patch("/{task_id}/renew", response_model=TaskRead)
def renew_task_router(
    project: Project = Depends(require_can_take_tasks),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    task: Task = Depends(get_task_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return renew_task(task, user, db)
