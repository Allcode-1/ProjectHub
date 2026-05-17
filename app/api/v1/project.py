from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.dependencies import get_current_active_user
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User

from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.project_member import ProjectMemberRead

from app.services.project_membership import can_view_project


router = APIRouter()


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def add_project(
    payload: ProjectCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project = Project(
        owner_id=user.id, name=payload.name, description=payload.description
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


@router.get("/", response_model=list[ProjectRead])
def get_projects(
    user: User = Depends(get_current_active_user)
):

    return user.projects


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project = db.scalar(select(Project).where(Project.id == project_id))

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_view_project(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project = db.scalar(
        select(Project).where(Project.owner_id == user.id, Project.id == project_id)
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    db.delete(project)
    db.commit()

    return None


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project = db.scalar(
        select(Project).where(Project.owner_id == user.id, Project.id == project_id)
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    updated_fields = payload.model_dump(exclude_unset=True)

    for field, value in updated_fields.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return project


@router.get("/{project_id}/members", response_model=list[ProjectMemberRead])
def get_project_members(
    project_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project = db.scalar(select(Project).where(Project.id == project_id))

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_view_project(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    project_members = db.scalars(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.user_id)
    ).all()

    return project_members


@router.get("/{project_id}/members/{member_id}", response_model=ProjectMemberRead)
def get_project_member(
    project_id: int,
    member_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    project = db.scalar(select(Project).where(Project.id == project_id))

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_view_project(db, user, project):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    project_member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == member_id
        )
    )

    if project_member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    return project_member
