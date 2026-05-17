from datetime import datetime

from pydantic import BaseModel

from app.models.project_invite import ProjectInviteAccessLevel


class ProjectMemberCreate(BaseModel):
    project_id: int
    user_id: int
    role: ProjectInviteAccessLevel


class ProjectMemberRead(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: ProjectInviteAccessLevel
    joined_at: datetime
