from __future__ import annotations
from typing import TYPE_CHECKING

from enum import Enum

from sqlalchemy import ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project


class ProjectInviteAccessLevel(str, Enum):
    VIEWER = "viewer"
    WORKER = "worker"
    ADMIN = "admin"


class ProjectInviteStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    REVOKED = "revoked"


class ProjectInvite(Base):
    __tablename__ = "project_invites"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    send_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    send_to: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    access_level: Mapped[ProjectInviteAccessLevel] = mapped_column(
        SAEnum(
            ProjectInviteAccessLevel,
            name="project_invite_access_level",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=ProjectInviteAccessLevel.VIEWER,
    )

    status: Mapped[ProjectInviteStatus] = mapped_column(
        SAEnum(
            ProjectInviteStatus,
            name="project_invite_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=ProjectInviteStatus.PENDING,
    )

    project: Mapped["Project"] = relationship(back_populates="project_invites")

    sender: Mapped["User"] = relationship(
        back_populates="sent_project_invites",
        foreign_keys=[send_by],
    )

    recipient: Mapped["User"] = relationship(
        back_populates="received_project_invites",
        foreign_keys=[send_to],
    )
