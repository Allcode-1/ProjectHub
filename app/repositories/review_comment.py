from sqlalchemy.orm import Session

from app.models.review_comment import ReviewComment


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
