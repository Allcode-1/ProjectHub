# Architecture

## Overview

ProjectHub is a synchronous FastAPI backend for managing projects, members,
sprints, tasks, reviews, and project invitations.

PostgreSQL is the source of truth. Redis is currently used for list caching and
login rate limiting.

```text
Client
  |
  v
FastAPI router
  |
  +-> Dependencies: authentication, RBAC, resource loading
  |
  v
Service: business rules and transaction boundary
  |
  v
Repository: SQLAlchemy queries
  |
  v
PostgreSQL

Query service -> Redis cache -> Repository fallback
```

## Main Components

| Component | Location | Responsibility |
|---|---|---|
| API routers | `app/api/v1/` | HTTP contract, dependencies, response models |
| Auth routes | `app/auth/` | Registration, login, refresh, logout |
| Dependencies | `app/dependencies/` | Authentication, RBAC, resource loading |
| Services | `app/services/` | Business actions, state transitions, transactions |
| Repositories | `app/repositories/` | Database reads and object creation |
| Models | `app/models/` | SQLAlchemy tables and enums |
| Schemas | `app/schemas/` | Pydantic request and response contracts |
| Cache | `app/cache/` | Redis keys, serialization, TTL, invalidation helpers |
| Database | `app/db/` | Engine, sessions, declarative base |
| Migrations | `alembic/` | Database schema history |
| Tests | `tests/` | Integration tests for API and domain behavior |

## Domain Structure

```text
Project
  |
  +-- contains -----------> Sprint
                             |
                             +-- contains -> Task
                                             |
                                             +-- has -> ReviewComment
```

Important ownership rules:

- A project has one owner.
- Project membership gives `viewer`, `worker`, or `admin` access.
- A sprint belongs to one project.
- A task belongs to one project and one sprint.
- A review comment belongs to one task.
- A task worker must be a worker of the same project when assigned through the
  API.

## Request Flow

### Command request

Example: decline a task with an optional comment.

1. The router authenticates the user.
2. Dependencies load the project, sprint, and task.
3. RBAC dependencies require owner/admin access.
4. The service validates the task state.
5. The service optionally creates a review comment.
6. The service changes the task status to `REJECTED`.
7. Both changes are committed in one database transaction.

### Cached query

Project and sprint list queries use cache-aside behavior:

1. Try to read the list from Redis.
2. Validate cached JSON with Pydantic.
3. On a miss or invalid value, read from PostgreSQL.
4. Store the serialized response in Redis with TTL and jitter.

Cache read/write failures are logged and queries fall back to PostgreSQL.

## Authorization Boundaries

Authorization is split into two levels:

- Dependencies check project-level access such as view, task work, or
  management.
- Services check object-level and workflow rules such as task ownership and
  current status.

Resource dependencies also keep nested identifiers consistent:

```text
project_id -> sprint.project_id -> task.sprint_id/project_id
```

Detailed permissions are documented in [RBAC.md](RBAC.md).

## Transactions

Business services currently own transaction boundaries and call `commit()`
after successful state changes.

Examples:

- Accepting an invite and creating a project member are committed together.
- Declining a task and creating its optional review comment are committed
  together.
- Task status transitions are committed individually.

PostgreSQL remains authoritative even when Redis is unavailable.

## Authentication

- Access and refresh tokens use JWT.
- Tokens are signed with RS256 keys.
- Refresh sessions are persisted in PostgreSQL.
- Refresh rotation and logout revoke refresh sessions.
- Login rate limiting uses Redis keys for IP and username.

## Current Limitations

These are known hardening areas, not new domain features:

- Cache invalidation is not complete for every mutation.
- Rate limiting currently depends on Redis availability.
- Redis is not fully isolated in the test suite.
- Some database indexes, constraints, and delete cascades need review.
- Sprint transition checks are less strict than task transition checks.
- Review comments are currently returned only while their task is
  `REJECTED`.
- Background jobs, Docker, CI, and observability are not implemented yet.

## Planned Direction

The next development stage should improve depth:

2. Review database constraints, indexes, and cascades.
3. Complete cache invalidation and Redis fallback behavior.
4. Expand integration tests and fix test isolation.
5. Finish typing and naming cleanup.
6. Add Docker Compose and CI.
