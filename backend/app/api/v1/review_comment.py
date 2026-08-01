from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.errors import AppError
from backend.app.auth.dependencies import get_current_active_user
from backend.app.db.session import get_db
from backend.app.dependencies.pagination import Pagination, get_pagination
from backend.app.dependencies.project import require_can_take_tasks
from backend.app.dependencies.sprint import get_sprint_by_id_or_404
from backend.app.models.project import Project
from backend.app.models.sprint import Sprint
from backend.app.models.task import TaskStatus
from backend.app.models.user import User
from backend.app.repositories.review_comment import ReviewCommentRepository
from backend.app.repositories.task import TaskRepository
from backend.app.schemas.review_comments import ReviewCommentRead
from backend.app.services.review_comments import get_my_review_comments


router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_active_user)]
TakeTasksProject = Annotated[Project, Depends(require_can_take_tasks)]
CurrentSprint = Annotated[Sprint, Depends(get_sprint_by_id_or_404)]
PaginationDep = Annotated[Pagination, Depends(get_pagination)]


@router.get("/my_review_comments", response_model=list[ReviewCommentRead])
def get_my_review_comments_router(
    project: TakeTasksProject,
    sprint: CurrentSprint,
    user: CurrentUser,
    db: DbSession,
    pagination: PaginationDep,
):

    return get_my_review_comments(
        project, sprint, user, db, pagination.limit, pagination.offset
    )


@router.get("/my_review_comments/{comment_id}", response_model=ReviewCommentRead)
def get_my_review_comment_router(
    comment_id: int,
    project: TakeTasksProject,
    sprint: CurrentSprint,
    user: CurrentUser,
    db: DbSession,
):

    review_comment_repo = ReviewCommentRepository(db)
    task_repo = TaskRepository(db)

    review_comment = review_comment_repo.comment_by_id(comment_id)

    if review_comment is None:
        raise AppError(404, "Review comment not found")

    task = task_repo.task_by_id(project.id, sprint.id, review_comment.task_id)

    if task is None or task.worker_id != user.id or task.status != TaskStatus.REJECTED:
        raise AppError(404, "Review comment not found")

    return review_comment
