from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import CheckConstraint, ForeignKey, DateTime, Index, String, func

from backend.app.db.session import Base

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.project_member import ProjectMember
    from backend.app.models.project_invite import ProjectInvite


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("length(name) >= 3", name="ck_projects_name_min_length"),
        Index("ix_projects_owner_id", "owner_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(55), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project_members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )

    project_invites: Mapped[list["ProjectInvite"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )

    owner: Mapped["User"] = relationship(back_populates="projects")
