from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.task import Task, TaskStatus

from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

from app.services.project_membership import (
    can_view_project,
    can_take_tasks,
    can_manage_sprints,
)


router = APIRouter()


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def add_task(
    project_id: int,
    sprint_id: int,
    payload: TaskCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_project = db.scalar(select(Project).where(Project.id == project_id))

    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_manage_sprints(db, user, existing_project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    existing_sprint = db.scalar(select(Sprint).where(Sprint.project_id == project_id, Sprint.id == sprint_id))

    if existing_sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    task = Task(
        project_id=project_id,
        sprint_id=sprint_id,
        creator_id=user.id,
        worker_id=payload.worker_id,
        title=payload.title,
        description=payload.description,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get("/", response_model=list[TaskRead])
def get_tasks(
    project_id: int,
    sprint_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_project = db.scalar(select(Project).where(Project.id == project_id))

    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    existing_sprint = db.scalar(select(Sprint).where(Sprint.project_id == project_id, Sprint.id == sprint_id))

    if existing_sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_view_project(db, user, existing_project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    tasks = db.scalars(
        select(Task)
        .where(Task.project_id == project_id, Task.sprint_id == sprint_id)
        .order_by(Task.id)
    ).all()

    return tasks


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    project_id: int,
    sprint_id: int,
    task_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_project = db.scalar(select(Project).where(Project.id == project_id))

    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    existing_sprint = db.scalar(select(Sprint).where(Sprint.project_id == project_id, Sprint.id == sprint_id))

    if existing_sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found"
        )

    if not can_view_project(db, user, existing_project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    task = db.scalar(
        select(Task).where(
            Task.project_id == project_id,
            Task.sprint_id == sprint_id,
            Task.id == task_id,
        )
    )

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    project_id: int,
    sprint_id: int,
    task_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_project = db.scalar(select(Project).where(Project.id == project_id))

    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    existing_sprint = db.scalar(select(Sprint).where(Sprint.project_id == project_id, Sprint.id == sprint_id))

    if existing_sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found"
        )

    if not can_manage_sprints(db, user, existing_project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    task = db.scalar(
        select(Task).where(
            Task.project_id == project_id,
            Task.sprint_id == sprint_id,
            Task.id == task_id,
        )
    )

    db.delete(task)
    db.commit()

    return None


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    project_id: int,
    sprint_id: int,
    task_id: int,
    payload: TaskUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_project = db.scalar(select(Project).where(Project.id == project_id))

    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    existing_sprint = db.scalar(select(Sprint).where(Sprint.project_id == project_id, Sprint.id == sprint_id))

    if existing_sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_manage_sprints(db, user, existing_project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    task = db.scalar(
        select(Task).where(
            Task.project_id == project_id,
            Task.sprint_id == sprint_id,
            Task.id == task_id,
        )
    )

    updated_fields = payload.model_dump(exclude_unset=True)

    for field, value in updated_fields.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task


@router.patch("/take_task/{task_id}", response_model=TaskRead)
def take_task_to_work(
    project_id: int,
    sprint_id: int,
    task_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_project = db.scalar(select(Project).where(Project.id == project_id))

    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    existing_sprint = db.scalar(select(Sprint).where(Sprint.project_id == project_id, Sprint.id == sprint_id))

    if existing_sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_take_tasks(db, user, existing_project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    task = db.scalar(
        select(Task).where(
            Task.project_id == project_id,
            Task.sprint_id == sprint_id,
            Task.id == task_id,
        )
    )

    if task.worker_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task already taken"
        )

    task.worker_id = user.id
    task.status = TaskStatus.IN_PROGRESS

    db.commit()
    db.refresh(task)

    return task


@router.patch("/to_review/{task_id}", response_model=TaskRead)
def send_task_to_review(
    project_id: int,
    sprint_id: int,
    task_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_project = db.scalar(select(Project).where(Project.id == project_id))

    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    existing_sprint = db.scalar(select(Sprint).where(Sprint.project_id == project_id, Sprint.id == sprint_id))

    if existing_sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_take_tasks(db, user, existing_project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    task = db.scalar(
        select(Task).where(
            Task.project_id == project_id,
            Task.sprint_id == sprint_id,
            Task.id == task_id,
        )
    )

    if task.worker_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task is not yours"
        )

    task.status = TaskStatus.REVIEW

    db.commit()
    db.refresh(task)

    return task


@router.patch("/accept/{task_id}", response_model=TaskRead)
def accept_task_review(
    project_id: int,
    sprint_id: int,
    task_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_project = db.scalar(select(Project).where(Project.id == project_id))

    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    existing_sprint = db.scalar(select(Sprint).where(Sprint.project_id == project_id, Sprint.id == sprint_id))

    if existing_sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_manage_sprints(db, user, existing_project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    task = db.scalar(
        select(Task).where(
            Task.project_id == project_id,
            Task.sprint_id == sprint_id,
            Task.id == task_id,
        )
    )

    if task.worker_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Can't accept your own task"
        )

    if task.status != TaskStatus.REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task need to be on review"
        )

    task.status = TaskStatus.DONE

    db.commit()
    db.refresh(task)

    return task


@router.patch("/decline/{task_id}", response_model=TaskRead)
def decline_task_review(
    project_id: int,
    sprint_id: int,
    task_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_project = db.scalar(select(Project).where(Project.id == project_id))

    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    existing_sprint = db.scalar(select(Sprint).where(Sprint.project_id == project_id, Sprint.id == sprint_id))

    if existing_sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_manage_sprints(db, user, existing_project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    task = db.scalar(
        select(Task).where(
            Task.project_id == project_id,
            Task.sprint_id == sprint_id,
            Task.id == task_id,
        )
    )

    if task.worker_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Can't decline your own task"
        )

    if task.status != TaskStatus.REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task need to be on review"
        )

    task.status = TaskStatus.REJECTED

    db.commit()
    db.refresh(task)

    return task


# TODO: individual endpoints for in_progress, done, rejected tasks or filter
# TODO: "/tasks/mine" for tasks that i created
# TODO: "/tasks/my_workspace" for tasks that i working on
# TODO: add comments to task accept/decline for workflow improving
