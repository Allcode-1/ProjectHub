from fastapi import APIRouter

from app.api.v1 import project
from app.api.v1 import sprint
from app.api.v1 import project_invite
from app.api.v1 import task

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(project.router, prefix="/projects", tags=["projects"])
v1_router.include_router(
    sprint.router, prefix="/projects/{project_id}/sprints", tags=["sprints"]
)
v1_router.include_router(project_invite.router, tags=["project invites"])
v1_router.include_router(
    task.router,
    prefix="/projects/{project_id}/sprints/{sprint_id}/tasks",
    tags=["tasks"],
)
