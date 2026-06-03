from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db.session import get_db

from app.models.user import User
from app.models.task import Task
from app.models.project import Project
from app.models.sprint import Sprint

from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

from app.services.task_actions import (
    add_task,
    update_task,
    delete_task,
    take_task_to_work,
    send_task_to_review,
    accept_task_review,
    decline_task_review,
)

from app.repositories.task import TaskRepository

from app.dependencies.project import (
    require_can_take_tasks,
    require_can_manage_sprints,
    require_can_view_project,
)
from app.dependencies.sprint import get_sprint_by_id_or_404
from app.dependencies.task import get_task_by_id_or_404


router = APIRouter()


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def add_task_router(
    payload: TaskCreate,
    project: Project = Depends(require_can_manage_sprints),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return add_task(payload, project, sprint, user, db)


@router.get("/", response_model=list[TaskRead])
def get_tasks_router(
    project: Project = Depends(require_can_view_project),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    task_repo = TaskRepository(db)
    tasks = task_repo.all_tasks_of_sprint(project.id, sprint.id)
    return tasks


@router.get("/{task_id}", response_model=TaskRead)
def get_task_router(
    project: Project = Depends(require_can_view_project),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    task: Task = Depends(get_task_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_router(
    project: Project = Depends(require_can_manage_sprints),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    task: Task = Depends(get_task_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return delete_task(task, user, db)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task_router(
    payload: TaskUpdate,
    project: Project = Depends(require_can_manage_sprints),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    task: Task = Depends(get_task_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return update_task(payload, task, user, db)


@router.patch("/{task_id}/take_task", response_model=TaskRead)
def take_task_to_work_router(
    project: Project = Depends(require_can_take_tasks),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    task: Task = Depends(get_task_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return take_task_to_work(task, user, db)


@router.patch("/{task_id}/to_review", response_model=TaskRead)
def send_task_to_review_router(
    project: Project = Depends(require_can_take_tasks),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    task: Task = Depends(get_task_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return send_task_to_review(task, user, db)


@router.patch("/{task_id}/accept", response_model=TaskRead)
def accept_task_review_router(
    project: Project = Depends(require_can_manage_sprints),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    task: Task = Depends(get_task_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return accept_task_review(task, user, db)


@router.patch("/{task_id}/decline", response_model=TaskRead)
def decline_task_review_router(
    project: Project = Depends(require_can_manage_sprints),
    sprint: Sprint = Depends(get_sprint_by_id_or_404),
    task: Task = Depends(get_task_by_id_or_404),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return decline_task_review(task, user, db)


# TODO: individual endpoints for in_progress, done, rejected tasks or filter
# TODO: "/tasks/mine" for tasks that i created
# TODO: "/tasks/my_workspace" for tasks that i working on
# TODO: add comments to task accept/decline for workflow improving
