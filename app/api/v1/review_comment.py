from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db.session import get_db
from app.dependencies.project import require_can_take_tasks
from app.dependencies.sprint import get_sprint_by_id_or_404
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.task import TaskStatus
from app.models.user import User
from app.repositories.review_comment import ReviewCommentRepository
from app.repositories.task import TaskRepository
from app.schemas.review_comments import ReviewCommentRead
from app.services.review_comments import get_my_review_comments


router = APIRouter()


@router.get("/my_review_comments", response_model=list[ReviewCommentRead])
def get_my_review_comments_router(
    project: Project = Depends(require_can_take_tasks),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return get_my_review_comments(project, sprint, user, db)


@router.get("/my_review_comments/{comment_id}", response_model=ReviewCommentRead)
def get_my_review_comment_router(
    comment_id: int,
    project: Project = Depends(require_can_take_tasks),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    review_comment_repo = ReviewCommentRepository(db)
    task_repo = TaskRepository(db)

    review_comment = review_comment_repo.comment_by_id(comment_id)

    if review_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review comment not found",
        )

    task = task_repo.task_by_id(project.id, sprint.id, review_comment.task_id)

    if task is None or task.worker_id != user.id or task.status != TaskStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review comment not found",
        )

    return review_comment
