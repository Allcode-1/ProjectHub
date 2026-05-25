from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, owner_id: int, name: str, description: str | None) -> Project:

        project = Project(owner_id=owner_id, name=name, description=description)

        self.db.add(project)
        return project

    def get_by_id(self, project_id: int) -> Project:
        return self.db.scalar(select(Project).where(Project.id == project_id))

    def list_owned_by_user(self, user_id: int) -> list[Project]:
        return self.db.scalars(
            select(Project).where(Project.owner_id == user_id).order_by(Project.id)
        ).all()

    def list_accessible_by_user(self, user_id: int) -> list[Project]:

        member_project_ids = select(ProjectMember.project_id).where(
            ProjectMember.user_id == user_id
        )

        return self.db.scalars(
            select(Project)
            .where(or_(Project.owner_id == user_id, Project.id.in_(member_project_ids)))
            .order_by(Project.id)
        ).all()

    def list_project_members(self, project_id: int) -> list[User]:

        return list(
            self.db.scalars(
                select(User)
                .join(ProjectMember, User.id == ProjectMember.user_id)
                .where(ProjectMember.project_id == project_id)
                .order_by(User.id)
            ).all()
        )
