# RBAC

## Scope

ProjectHub has project-level RBAC. A user's global account role is separate
from their access inside a project.

The project owner is stored in `projects.owner_id`. Other project roles are
stored in `project_members`.

## Roles

- `owner`: owns the project and controls project-level settings.
- `admin`: manages invites, sprints, tasks, and task reviews.
- `worker`: takes tasks, works on assigned tasks, and reads decline comments.
- `viewer`: read-only access to project data.

## Permission Levels

The code currently groups permissions into three reusable checks:

| Permission | Owner | Admin | Worker | Viewer |
|---|:---:|:---:|:---:|:---:|
| `can_view_project` | Yes | Yes | Yes | Yes |
| `can_take_tasks` | Yes | Yes | Yes | No |
| `can_manage_sprints` | Yes | Yes | No | No |

These checks only grant project-level access. Services still validate task
ownership, invite ownership, and workflow status.

## Project Permissions

| Action | Owner | Admin | Worker | Viewer | Conditions |
|---|:---:|:---:|:---:|:---:|---|
| Create a project | Yes | Yes | Yes | Yes | Any authenticated user creates a project as its owner |
| List accessible projects | Yes | Yes | Yes | Yes | Returns owned and joined projects |
| View project | Yes | Yes | Yes | Yes | Must belong to the project |
| View project members | Yes | Yes | Yes | Yes | Must belong to the project |
| Update project | Yes | No | No | No | Service requires `project.owner_id == user.id` |
| Delete project | Yes | No | No | No | Service requires `project.owner_id == user.id` |

## Invite And Access Permissions

| Action | Owner | Admin | Worker | Viewer | Conditions |
|---|:---:|:---:|:---:|:---:|---|
| Create invite | Yes | Yes | No | No | Recipient is not already a member or invited |
| Update invite | Yes | Yes | No | No | Actor must also be the original invite sender |
| Delete invite | Yes | Yes | No | No | Actor must also be the original invite sender |
| List received invites | Yes | Yes | Yes | Yes | Only the current user's invites |
| Read received invite | Yes | Yes | Yes | Yes | User must be the invite recipient |
| Accept invite | Yes | Yes | Yes | Yes | Recipient only; invite must be `PENDING` |
| Decline invite | Yes | Yes | Yes | Yes | Recipient only; invite must be `PENDING` |

Role columns in this table describe the actor's project role where one exists.
Users without project access can still accept or decline an invite addressed to
them.

## Sprint Permissions

| Action | Owner | Admin | Worker | Viewer | Conditions |
|---|:---:|:---:|:---:|:---:|---|
| List or view sprints | Yes | Yes | Yes | Yes | Must belong to the project |
| Create sprint | Yes | Yes | No | No | Project management permission |
| Update sprint | Yes | Yes | No | No | Project management permission |
| Delete sprint | Yes | Yes | No | No | Project management permission |
| Start sprint | Yes | Yes | No | No | Must satisfy sprint transition rules |
| Close sprint | Yes | Yes | No | No | Must satisfy sprint transition rules |

## Task Permissions

| Action | Owner | Admin | Worker | Viewer | Conditions |
|---|:---:|:---:|:---:|:---:|---|
| List or view tasks | Yes | Yes | Yes | Yes | Must belong to project and sprint |
| Create task | Yes | Yes | No | No | Assigned worker must belong to the project |
| Update task | Yes | Yes | No | No | New worker must belong to the project |
| Delete task | Yes | Yes | No | No | Project management permission |
| View tasks created by self | Yes | Yes | No | No | `/tasks/mine` |
| View assigned workspace | Yes | Yes | Yes | No | Filters by current user's `worker_id` |
| Take task | Yes | Yes | Yes | No | `TODO`; free or assigned to current user |
| Send to review | Yes | Yes | Yes | No | Current user must be the assigned worker |
| Accept task | Yes | Yes | No | No | Task must be `REVIEW` |
| Decline task | Yes | Yes | No | No | Task must be `REVIEW`; comment is optional |
| Resume rejected task | Yes | Yes | Yes | No | Current user must be the assigned worker |

Owner and admin can perform worker actions only when they are actually assigned
to the task where the service requires `task.worker_id == user.id`.

## Review Comment Permissions

| Action | Owner | Admin | Worker | Viewer | Conditions |
|---|:---:|:---:|:---:|:---:|---|
| Create decline comment | Yes | Yes | No | No | Created atomically during task decline |
| List own review comments | Conditional | Conditional | Yes | No | User must be the assigned worker of a `REJECTED` task |
| Read own review comment | Conditional | Conditional | Yes | No | Same assigned-worker and status checks |

There is no standalone comment creation endpoint. Comments are currently
created only as part of the decline action.

## Object-Level Rules

- Nested project, sprint, and task identifiers must describe the same object
  hierarchy.
- A task can be taken only if it is free or already assigned to the actor.
- Only the assigned worker can send, resume, or read review comments for a task.
- An assigned worker must belong to the task's project when assigned through
  create or update endpoints.
- Invite and review comment lookups return `404` when the object does not belong
  to the current user.
- Project update and delete are owner-only even though the router first accepts
  project managers.

## Enforcement Locations

- `app/dependencies/project.py`: project-level RBAC.
- `app/dependencies/sprint.py`: project/sprint consistency.
- `app/dependencies/task.py`: project/sprint/task consistency.
- `app/services/project_membership.py`: permission functions.
- Action services: object ownership and workflow state checks.

## Rules To Review

- Decide whether owner/admin should be allowed to take worker tasks.
- Decide whether admins should update/delete projects or remain blocked by the
  owner-only service rule.
- Decide whether invite management should depend on the original sender or any
  project manager.
- Decide whether review comment history remains readable after task resume.
- Add a full allowed/forbidden role test matrix for every command endpoint.
