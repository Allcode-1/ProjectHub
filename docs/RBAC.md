# RBAC

## Scope

ProjectHub has two authorization layers:

- Global account role in `users.role`, currently used for admin-only user
  listing.
- Project-level role for each project workspace.

The project owner is stored in `projects.owner_id`. Other project roles are
stored in `project_members`. Services can be stricter than routers, so the
matrix below documents the effective behavior of the current backend.

## Roles

| Role | Meaning |
|---|---|
| `owner` | Owns the project and controls owner-only project settings |
| `admin` | Manages invites, sprints, tasks, and task reviews |
| `worker` | Takes tasks, works on assigned tasks, and reads own decline comments |
| `viewer` | Reads project data only |

`owner` is not stored as a `project_members.role`. It is derived from
`projects.owner_id == user.id`.

## Permission Helpers

| Helper | Owner | Admin | Worker | Viewer | Outside |
|---|:---:|:---:|:---:|:---:|:---:|
| `can_view_project` | Yes | Yes | Yes | Yes | No |
| `can_take_tasks` | Yes | Yes | Yes | No | No |
| `can_manage_sprints` | Yes | Yes | No | No | No |

These helpers grant project-level access only. Object ownership, task
assignment, invite sender, and workflow state are enforced in services.

## Global Auth Matrix

| Action | Anonymous | Active user | Global admin | Conditions |
|---|:---:|:---:|:---:|---|
| Register | Yes | Yes | Yes | Username/email must be unique |
| Login | Yes | Yes | Yes | Redis rate limit by IP and username |
| Refresh token | Yes | Yes | Yes | Refresh token must be active and not reused |
| Logout | Yes | Yes | Yes | Refresh token must be valid and active |
| Get current user | No | Yes | Yes | Access token must be valid |
| List users | No | No | Yes | Requires `users.role == admin` |

## Project And Member Matrix

| Action | Owner | Admin | Worker | Viewer | Outside | Conditions |
|---|:---:|:---:|:---:|:---:|:---:|---|
| Create project | Yes | Yes | Yes | Yes | Yes | Any authenticated user becomes owner |
| List accessible projects | Yes | Yes | Yes | Yes | No | Returns owned and joined projects |
| View project | Yes | Yes | Yes | Yes | No | Must have project access |
| View project members | Yes | Yes | Yes | Yes | No | Must have project access |
| Update project | Yes | No | No | No | No | Service requires project owner |
| Delete project | Yes | No | No | No | No | Service requires project owner |
| Leave project | No | Yes | Yes | Yes | No | Owner cannot leave; member cannot have active assigned tasks |

The router for project update/delete accepts project managers, but the service
keeps these actions owner-only.

## Invite Matrix

| Action | Owner | Admin | Worker | Viewer | Recipient outside project | Conditions |
|---|:---:|:---:|:---:|:---:|:---:|---|
| Create invite | Yes | Yes | No | No | No | Recipient is not already a member and has no pending invite |
| Update invite | Conditional | Conditional | No | No | No | Owner/admin must also be original invite sender |
| Delete invite | Conditional | Conditional | No | No | No | Owner/admin must also be original invite sender |
| List received invites | Yes | Yes | Yes | Yes | Yes | Only current user's received invites |
| Read received invite | Yes | Yes | Yes | Yes | Yes | Current user must be invite recipient |
| Accept invite | Yes | Yes | Yes | Yes | Yes | Recipient only; invite must be `PENDING` |
| Decline invite | Yes | Yes | Yes | Yes | Yes | Recipient only; invite must be `PENDING` |

Invite accept/decline locks the invite row. Accepting an invite creates project
membership in the same transaction and invalidates the recipient project-list
cache.

## Sprint Matrix

| Action | Owner | Admin | Worker | Viewer | Outside | Conditions |
|---|:---:|:---:|:---:|:---:|:---:|---|
| List sprints | Yes | Yes | Yes | Yes | No | Must have project access |
| View sprint | Yes | Yes | Yes | Yes | No | Sprint must belong to project |
| Create sprint | Yes | Yes | No | No | No | Valid date range |
| Update sprint | Yes | Yes | No | No | No | Closed sprint cannot be updated |
| Delete sprint | Yes | Yes | No | No | No | Sprint must belong to project |
| Start sprint | Yes | Yes | No | No | No | Only `PLANNED`; not already ended |
| Close sprint | Yes | Yes | No | No | No | Only `ACTIVE` |

Current sprint workflow:

```text
PLANNED -> ACTIVE -> CLOSED
```

## Task Read Matrix

| Action | Owner | Admin | Worker | Viewer | Outside | Conditions |
|---|:---:|:---:|:---:|:---:|:---:|---|
| List all sprint tasks | Yes | Yes | Yes | Yes | No | Project/sprint consistency required |
| View task | Yes | Yes | Yes | Yes | No | Project/sprint/task consistency required |
| List tasks by status | Yes | Yes | Yes | Yes | No | `todo`, `in_progress`, `review`, `done`, `rejected` |
| View tasks created by self | Yes | Yes | No | No | No | Route requires project management access |
| View assigned workspace | Yes | Yes | Yes | No | No | Returns tasks assigned to current user |

## Task Command Matrix

| Action | Owner | Admin | Worker | Viewer | Outside | Conditions |
|---|:---:|:---:|:---:|:---:|:---:|---|
| Create task | Yes | Yes | No | No | No | Sprint must be open; assigned worker must belong to project |
| Update task | Yes | Yes | No | No | No | Sprint open; task locked; only `TODO` tasks can be edited |
| Delete task | Yes | Yes | No | No | No | Sprint open; task locked; only `TODO` tasks can be deleted |
| Take task | Yes | Yes | Yes | No | No | Sprint open; task `TODO`; task free or already assigned to actor |
| Send task to review | Conditional | Conditional | Conditional | No | No | Actor must be assigned worker; task `IN_PROGRESS` |
| Accept task review | Yes | Yes | No | No | No | Sprint open; task `REVIEW`; reviewer cannot be assigned worker |
| Decline task review | Yes | Yes | No | No | No | Sprint open; task `REVIEW`; reviewer cannot be assigned worker |
| Resume rejected task | Conditional | Conditional | Conditional | No | No | Actor must be assigned worker; task `REJECTED` |

Owner/admin can reach worker-action routes at the project-permission level, but
assigned-worker service rules still apply for send-to-review and renew.

Current task workflow:

```text
TODO -> IN_PROGRESS -> REVIEW -> DONE
REVIEW -> REJECTED -> IN_PROGRESS
```

## Review Comment Matrix

| Action | Owner | Admin | Worker | Viewer | Outside | Conditions |
|---|:---:|:---:|:---:|:---:|:---:|---|
| Create decline comment | Yes | Yes | No | No | No | Created only during task decline |
| List own review comments | Conditional | Conditional | Conditional | No | No | Actor must be assigned worker of rejected tasks |
| Read own review comment | Conditional | Conditional | Conditional | No | No | Comment task must be assigned to actor and `REJECTED` |

There is no standalone comment creation endpoint. Comments are created only as
part of the decline action.

## Object-Level Rules

- Nested project, sprint, and task identifiers must describe the same hierarchy.
- A task can be taken only if it is free or already assigned to the actor.
- Only the assigned worker can send a task to review, renew a rejected task, or
  read review comments for that task.
- The assigned worker must belong to the task's project when assigned through
  create or update endpoints.
- A reviewer cannot accept or decline their own task.
- Invite and review comment lookups return `404` when the object does not
  belong to the current user.
- Project update and delete are owner-only at service level.
- Project owner self-leave is blocked.
- Member self-leave is blocked while the user has active assigned tasks.
- Closed sprints block task commands and sprint updates.

## Enforcement Locations

| Concern | Location |
|---|---|
| Current user and global admin | `app/auth/dependencies.py` |
| Project-level RBAC | `app/dependencies/project.py` |
| Sprint/project consistency | `app/dependencies/sprint.py` |
| Task/project/sprint consistency | `app/dependencies/task.py` |
| Project role helpers | `app/services/project_membership.py` |
| Project owner-only rules | `app/services/project_actions.py` |
| Member self-leave rules | `app/services/project_members.py` |
| Invite sender/recipient/status rules | `app/services/project_invites.py` |
| Sprint state machine | `app/services/sprint_actions.py` |
| Task state machine | `app/services/task_actions.py` |
| Review comment visibility | `app/services/review_comments.py` |

## Test Coverage Direction

The current tests cover important positive, negative, and concurrency-sensitive
paths. The next RBAC hardening step is a table-driven forbidden/allowed matrix
test suite that iterates every command endpoint across owner, admin, worker,
viewer, and outside users.
