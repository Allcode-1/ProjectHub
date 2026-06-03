from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.models.project import Project
from app.models.sprint import Sprint

from app.schemas.sprint import SprintCreate, SprintRead, SprintUpdate

from app.services.sprint_actions import (
    create_sprint,
    update_sprint,
    delete_sprint,
    start_sprint,
    close_sprint,
)

from app.repositories.sprint import SprintRepository

from app.dependencies.sprint import get_sprint_by_id_or_404
from app.dependencies.project import (
    require_can_manage_sprints,
    require_can_view_project,
)


router = APIRouter()


@router.post("/", response_model=SprintRead, status_code=status.HTTP_201_CREATED)
def add_sprint_router(
    payload: SprintCreate,
    project: Project = Depends(require_can_manage_sprints),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return create_sprint(payload, project, user, db)


@router.get("/", response_model=list[SprintRead])
def get_sprints_router(
    project: Project = Depends(require_can_view_project),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    sprint_repo = SprintRepository(db)
    sprints = sprint_repo.all_sprints(project.id)

    return sprints


@router.get("/{sprint_id}", response_model=SprintRead)
def get_sprint_router(
    project: Project = Depends(require_can_view_project),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return sprint


@router.delete("/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sprint_router(
    project: Project = Depends(require_can_manage_sprints),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return delete_sprint(project, sprint, user, db)


@router.patch("/{sprint_id}", response_model=SprintRead)
def update_sprint_router(
    payload: SprintUpdate,
    project: Project = Depends(require_can_manage_sprints),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return update_sprint(payload, project, sprint, user, db)


@router.patch("/{sprint_id}/start", response_model=SprintRead)
def start_sprint_router(
    project: Project = Depends(require_can_manage_sprints),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return start_sprint(project, sprint, user, db)


@router.patch("/{sprint_id}/close", response_model=SprintRead)
def close_sprint_rputer(
    project: Project = Depends(require_can_manage_sprints),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return close_sprint(project, sprint, user, db)
