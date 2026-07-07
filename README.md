# ProjectHub

ProjectHub is a FastAPI backend API for Jira-like project management workflows.

This project is built as a backend engineering portfolio project, focused on
authentication, project-level RBAC, domain workflows, PostgreSQL modeling,
Redis, Celery, Docker Compose, and integration testing.

## Engineering Focus

- RS256 JWT authentication with refresh-session rotation.
- Project-level RBAC: owner, admin, worker, viewer.
- Invite-based project membership.
- Sprint lifecycle: planned, active, closed.
- Task workflow: TODO -> IN_PROGRESS -> REVIEW -> DONE / REJECTED.
- Review comments created during task decline.
- Transaction boundaries in the service layer.
- Redis cache-aside for project and sprint lists.
- Redis-backed login rate limiting.
- Celery Beat + RabbitMQ sprint lifecycle job.
- PostgreSQL schema with SQLAlchemy 2 and Alembic.
- Docker Compose environment.
- Pytest integration coverage.

## Domain Model

ProjectHub models a project workspace where users create projects as owners,
owners and admins invite teammates, members receive project-level roles,
managers create sprints and tasks, workers take tasks and send them to review,
and owners/admins accept or decline reviewed tasks.

Declined tasks can receive review comments, which gives workers a simple
feedback loop before resuming the task.

Task workflow:

```text
TODO -> IN_PROGRESS -> REVIEW -> DONE
REVIEW -> REJECTED -> IN_PROGRESS
```

Sprint workflow:

```text
PLANNED -> ACTIVE -> CLOSED
```

## Backend Design

Business logic lives in services, repositories isolate SQLAlchemy access, and
dependencies handle authentication, authorization, and nested resource loading.
Redis and Celery are used where they support the domain: cached reads, login
rate limiting, and scheduled sprint lifecycle synchronization.

## Engineering Decisions

**Why RS256 instead of HS256?**
RS256 keeps signing and verification responsibilities separate through a private
and public key pair. That is more infrastructure than a shared secret, but it
shows a realistic token setup where only the auth server needs the private key.
For this project, it is mainly an engineering exercise in asymmetric JWTs.

**Why split services and repositories?**
Workflow rules such as task review, invite acceptance, and sprint transitions
belong in services because they combine validation, state changes, and
transactions. Repositories stay focused on SQLAlchemy queries, which keeps route
handlers thin and makes business logic easier to inspect.

**Why cache-aside instead of write-through?**
Project and sprint lists are read-heavy and easy to rebuild from PostgreSQL.
Cache-aside keeps PostgreSQL as the source of truth, lets Redis fail open for
queries, and makes invalidation explicit after key mutations.

## Authentication

The authentication flow includes user registration, login, bcrypt password
hashing, RS256 access/refresh JWTs, refresh sessions stored in PostgreSQL,
refresh-token rotation, logout/revoke, and a current-user endpoint.

Login is protected by Redis-backed rate limiting using both client IP and
username keys.

## Authorization / RBAC

ProjectHub uses project-level roles:

- `owner`: owns the project and controls project-level settings.
- `admin`: manages invites, sprints, tasks, and task reviews.
- `worker`: takes tasks, works on assigned tasks, and reads decline comments.
- `viewer`: has read-only access to project data.

Project-level permissions are checked in dependencies, while object-level rules
are enforced in services. The API also validates nested resource consistency:

```text
project_id -> sprint_id -> task_id
```

Task actions include assigned-worker checks, and invite actions are restricted
to the invite recipient where appropriate.

More details are documented in [RBAC](docs/RBAC.md).

## Workflow Logic

Task services validate allowed state transitions:

- take a TODO task into work;
- send an assigned task to review;
- accept reviewed work;
- decline reviewed work with an optional review comment;
- resume a rejected task.

Sprint services support sprint creation, manual start, manual close, and
periodic lifecycle synchronization through Celery Beat.

## Redis

Redis is used in two places:

- cache-aside reads for project and sprint lists;
- login rate limiting by IP and username.

Cached values are JSON-serialized, validated with Pydantic on read, stored with
TTL + jitter, and invalidated after key mutations. Cached queries are designed
to fail open: if Redis cache access fails, the API falls back to PostgreSQL.

Limitation: cache invalidation is implemented for key flows, but it is not yet a
full universal cache strategy for every possible mutation.

## Celery / Background Jobs

The Docker Compose stack includes RabbitMQ, a Celery worker, and Celery Beat.
Celery Beat schedules a sprint lifecycle synchronization job that periodically:

- activates planned sprints whose start time has arrived;
- closes planned/active sprints whose end time has passed;
- invalidates affected sprint-list cache keys.

Limitation: Celery is currently used for sprint lifecycle synchronization, not
for a broad background job system yet.

## Testing

The test suite uses pytest integration tests for the core API flows:

- auth, login, refresh rotation, logout/revoke;
- projects and project visibility;
- invites and membership;
- sprints;
- tasks and task workflow actions;
- review comments;
- cache invalidation;
- Celery schedule and sprint lifecycle idempotency.

Redis is isolated in tests with an in-memory fake. Tests cover the main flows,
but this is not a complete permission and concurrency matrix yet. Concurrency
tests and a full RBAC permission matrix are planned.

Run tests:

```bash
uv run pytest
```

Run linting and type checks:

```bash
uv run ruff check .
uv run mypy app tests
```

## Docker Compose

The repository includes a Docker Compose environment for the API, PostgreSQL,
Redis, RabbitMQ, Celery worker, and Celery Beat.

Generate JWT keys in `certs/`, then start the stack and run migrations:

```bash
mkdir -p certs
openssl genrsa -out certs/private.pem 2048
openssl rsa -in certs/private.pem -pubout -out certs/public.pem
docker compose up -d db redis rabbitmq
docker compose run --rm api uv run alembic upgrade head
docker compose up -d api worker beat
```

Check the API:

```bash
curl http://localhost:8000/health
```

Interactive API docs:

```text
http://localhost:8000/docs
```

## Local Development

Create a `.env` file for non-Docker runs:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/project_hub
TEST_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/project_hub_test
REDIS_URL=redis://localhost:6390/0
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
```

Install dependencies:

```bash
uv sync
```

Run migrations:

```bash
uv run alembic upgrade head
```

Start the API:

```bash
uv run uvicorn app.main:app --reload
```

## API Overview

The API covers these main areas:

- Auth: register, login, refresh, logout, current user.
- Projects: create, read, update, delete, list accessible projects.
- Invites: invite users, accept/decline invites, list received invites.
- Sprints: create, update, start, close, list project sprints.
- Tasks: create, assign, filter by status, take to work, send to review,
  accept, decline, resume rejected tasks.
- Review comments: read decline comments visible to the assigned worker.

See the interactive OpenAPI documentation for the complete endpoint list:

```text
http://localhost:8000/docs
```

## Current Status

ProjectHub is an MVP / backend portfolio project.

Currently implemented:

- auth;
- project CRUD;
- invites;
- project roles;
- sprints;
- task workflow;
- Redis cache/rate limiting;
- Celery sprint lifecycle synchronization;
- Docker Compose;
- integration tests.

Needs hardening:

- sprint closing product flow;
- unfinished task migration between sprints;
- stricter task/sprint state machine;
- concurrency-safe task claiming;
- database constraints and indexes review;
- complete cache invalidation strategy;
- full RBAC matrix tests;
- production deployment docs and CI.

## Roadmap

### v0.2

- Stricter task/sprint state machine.
- Concurrency-safe task claiming.
- Database indexes and constraints review.
- Full RBAC matrix tests.
- Alembic migration tests.
- Better cache invalidation.

### v0.3

- Unfinished task migration between sprints.
- Better sprint closing report/results.
- CI workflow.
- Production Docker/Nginx docs.
- Observability and logging improvements.
- Expired refresh session cleanup.

## What This Project Is Not

- Not a production-ready Jira clone.
- Not a fullstack product.
- Not a microservice system.
- Not a complete RBAC platform.
- Not a high-traffic/load-testing project.
