from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.models.project import Project

from app.models.project_invite import ProjectInviteStatus
from app.models.project_invite import ProjectInvite
from app.models.project_member import ProjectMember
from app.schemas.project_invite import (
    ProjectInviteCreate,
    ProjectInviteRead,
    ProjectInviteUpdate,
)

from app.services.project_membership import can_manage_sprints

router = APIRouter()


@router.post(
    "/projects/{project_id}/invites/users/{recipient_id}",
    response_model=ProjectInviteRead,
    status_code=status.HTTP_201_CREATED,
)
def invite_user_to_project(
    project_id: int,
    recipient_id: int,
    payload: ProjectInviteCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_project = db.scalar(select(Project).where(Project.id == project_id))

    if not existing_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_manage_sprints(db, user, existing_project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    existing_recipient = db.scalar(select(User).where(User.id == recipient_id))

    if not existing_recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found"
        )

    existing_invite = db.scalar(
        select(ProjectInvite).where(
            ProjectInvite.project_id == project_id,
            ProjectInvite.send_by == user.id,
            ProjectInvite.send_to == recipient_id,
        )
    )

    if existing_invite:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already invited to this project",
        )

    project_invite = ProjectInvite(
        project_id=project_id,
        send_by=user.id,
        send_to=recipient_id,
        access_level=payload.access_level,
    )

    db.add(project_invite)
    db.commit()
    db.refresh(project_invite)

    return project_invite


@router.patch(
    "/projects/{project_id}/invites/users/{recipient_id}",
    response_model=ProjectInviteRead,
)
def update_user_invite(
    project_id: int,
    recipient_id: int,
    payload: ProjectInviteUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_project = db.scalar(select(Project).where(Project.id == project_id))

    if not existing_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_manage_sprints(db, user, existing_project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    existing_recipient = db.scalar(select(User).where(User.id == recipient_id))

    if not existing_recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found"
        )

    existing_invite = db.scalar(
        select(ProjectInvite).where(
            ProjectInvite.project_id == project_id,
            ProjectInvite.send_by == user.id,
            ProjectInvite.send_to == recipient_id,
        )
    )

    if not existing_invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found"
        )

    updated_fields = payload.model_dump(exclude_unset=True)

    for field, value in updated_fields.items():
        setattr(existing_invite, field, value)

    db.commit()
    db.refresh(existing_invite)

    return existing_invite


@router.delete(
    "/projects/{project_id}/invites/users/{recipient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user_invite(
    project_id: int,
    recipient_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_project = db.scalar(select(Project).where(Project.id == project_id))

    if not existing_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if not can_manage_sprints(db, user, existing_project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights"
        )

    existing_recipient = db.scalar(select(User).where(User.id == recipient_id))

    if not existing_recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found"
        )

    existing_invite = db.scalar(
        select(ProjectInvite).where(
            ProjectInvite.project_id == project_id,
            ProjectInvite.send_by == user.id,
            ProjectInvite.send_to == recipient_id,
        )
    )

    if not existing_invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found"
        )

    db.delete(existing_invite)
    db.commit()

    return None


@router.get("/invites", response_model=list[ProjectInviteRead])
def get_my_invites(
    user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):

    my_invites = db.scalars(
        select(ProjectInvite).where(ProjectInvite.send_to == user.id)
    ).all()

    return my_invites


@router.get("/invites/{invite_id}", response_model=ProjectInviteRead)
def get_invite_by_id(
    invite_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    invite = db.scalar(
        select(ProjectInvite).where(
            ProjectInvite.send_to == user.id, ProjectInvite.id == invite_id
        )
    )

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found"
        )

    return invite


@router.patch("/invites/accept/{invite_id}", response_model=ProjectInviteRead)
def accept_invite(
    invite_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_invite = db.scalar(
        select(ProjectInvite).where(
            ProjectInvite.send_to == user.id, ProjectInvite.id == invite_id
        )
    )

    if not existing_invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found"
        )

    if existing_invite.status != ProjectInviteStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Invite already responced"
        )

    existing_invite.status = ProjectInviteStatus.ACCEPTED

    now = datetime.now(timezone.utc)

    new_project_member = ProjectMember(
        project_id=existing_invite.project_id,
        user_id=user.id,
        role=existing_invite.access_level,
        joined_at=now,
    )

    db.add(new_project_member)
    db.commit()
    db.refresh(existing_invite)

    return existing_invite


@router.patch("/invites/decline/{invite_id}", response_model=ProjectInviteRead)
def decline_invite(
    invite_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    existing_invite = db.scalar(
        select(ProjectInvite).where(
            ProjectInvite.send_to == user.id, ProjectInvite.id == invite_id
        )
    )

    if not existing_invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found"
        )

    if existing_invite.status != ProjectInviteStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Invite already responced"
        )

    existing_invite.status = ProjectInviteStatus.DECLINED

    db.commit()
    db.refresh(existing_invite)

    return existing_invite
