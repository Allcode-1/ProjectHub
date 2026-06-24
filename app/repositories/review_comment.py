from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review_comment import ReviewComment
from app.models.task import Task


class ReviewCommentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        task_id: int,
        comment: str,
        author_id: int,
    ) -> ReviewComment:
        review_comment = ReviewComment(
            task_id=task_id,
            comment=comment,
            author_id=author_id,
        )

        self.db.add(review_comment)
        return review_comment

    def comment_by_id(self, comment_id: int) -> ReviewComment | None:

        return self.db.scalar(
            select(ReviewComment).where(ReviewComment.id == comment_id)
        )

    def comments_by_task_ids(self, task_ids: list[int]) -> list[ReviewComment]:

        if not task_ids:
            return []

        return list(
            self.db.scalars(
                select(ReviewComment)
                .join(Task, ReviewComment.task_id == Task.id)
                .where(ReviewComment.task_id.in_(task_ids))
                .order_by(ReviewComment.id)
            ).all()
        )
