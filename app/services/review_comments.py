from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.review_comment import ReviewComment
from app.models.sprint import Sprint
from app.models.user import User
from app.repositories.review_comment import ReviewCommentRepository
from app.repositories.task import TaskRepository


def get_my_review_comments(
    project: Project,
    sprint: Sprint,
    user: User,
    db: Session,
) -> list[ReviewComment]:

    task_repo = TaskRepository(db)
    review_comment_repo = ReviewCommentRepository(db)

    tasks = task_repo.rejected_tasks_assigned_to_user(
        project.id,
        sprint.id,
        user.id,
    )
    task_ids = [task.id for task in tasks]

    return review_comment_repo.comments_by_task_ids(task_ids)
