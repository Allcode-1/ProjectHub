from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.project_invite import ProjectInvite


class ProjectInviteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_invite(
        self, project_id, user_id, recipient_id, access_level
    ) -> ProjectInvite:

        project_invite = ProjectInvite(
            project_id=project_id,
            send_by=user_id,
            send_to=recipient_id,
            access_level=access_level,
        )

        self.db.add(project_invite)
        return project_invite

    def invite_by_id(self, invite_id) -> ProjectInvite:

        return self.db.scalar(
            select(ProjectInvite).where(ProjectInvite.id == invite_id)
        )

    def invite_by_user_id(self, project_id, recipient_id) -> ProjectInvite:

        return self.db.scalar(
            select(ProjectInvite).where(
                ProjectInvite.project_id == project_id,
                ProjectInvite.send_to == recipient_id,
            )
        )

    def recipient_by_id(self, recipient_id):

        return self.db.scalar(select(User).where(User.id == recipient_id))

    def invites_to_user(self, recipient_id):
        return self.db.scalars(
            select(ProjectInvite)
            .where(ProjectInvite.send_to == recipient_id)
            .order_by(ProjectInvite.id)
        ).all()
