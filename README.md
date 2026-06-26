## ProjectHub

ProjectHub is a FastAPI backend for managing team projects in a Jira-like workflow.
It lets users create projects, invite teammates with project-level roles, plan
two-week sprints, create tasks, assign work, send tasks to review, and close sprint
workflows with visible progress for owners, admins, workers, and viewers.

### Status

MVP. The core API is implemented and covered by basic integration tests, but some
production-facing pieces still need hardening, especially cache invalidation,
test isolation for Redis, and more complete workflow rules.

### Core Features

- User registration and login.
- JWT access and refresh tokens with refresh-session rotation and logout revoke.
- Project CRUD for owners.
- Project invitations by user id.
- Project roles: owner, admin, worker, viewer.
- Role-based project access control.
- Sprint CRUD, start, and close actions.
- Task CRUD plus workflow actions: take task, send to review, accept, decline.
- Project and sprint list caching with Redis.
- Login rate limiting by IP and username.
- Alembic migrations for the database schema.
- Pytest integration tests for auth, projects, invites, sprints, and tasks.

### Tech Features

- CRUD+ domain workflows for projects, sprints, tasks, and invites.
- RBAC for project permissions.
- JWT auth with asymmetric RS256 keys.
- Refresh-token sessions stored in the database.
- Redis cache layer with JSON serialization, TTL, and jitter.
- Redis-backed rate limiting for login attempts.
- Repository/service/dependency split for cleaner API handlers.
- SQLAlchemy 2 typed models and Alembic migrations.
- Pydantic 2 request/response schemas.

### Tech Stack

- Python 3.13
- FastAPI
- Pydantic 2
- SQLAlchemy 2
- Alembic
- PostgreSQL
- Redis
- PyJWT
- bcrypt
- Uvicorn
- Pytest
- Ruff
- mypy
- uv

### Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [RBAC](docs/RBAC.md)

### Requirements

Create a `.env` file with at least:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/project_hub
TEST_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/project_hub_test
REDIS_URL=redis://localhost:6390/0
```

JWT keys are read from:

```text
certs/private.pem
certs/public.pem
```

### Quick Start

Install dependencies:

```bash
uv sync
```

Run migrations:

```bash
uv run alembic upgrade head
```

Start Redis and then run the API:

```bash
uv run uvicorn app.main:app --reload
```

Health check:

```bash
GET /health
```

Interactive API docs are available at:

```text
http://127.0.0.1:8000/docs
```

### Docker Compose

The repository includes a Docker setup for the API, PostgreSQL, and Redis.
Docker Compose provides container-local `DATABASE_URL` and `REDIS_URL` values,
so the `.env` file above is mainly needed for local non-Docker runs.

Make sure JWT keys exist on the host before starting the API because
`docker-compose.yml` mounts `./certs` into the container:

```bash
mkdir -p certs
openssl genrsa -out certs/private.pem 2048
openssl rsa -in certs/private.pem -pubout -out certs/public.pem
```

Build the API image:

```bash
docker compose build api
```

Start PostgreSQL and Redis:

```bash
docker compose up -d db redis
```

Run database migrations:

```bash
docker compose run --rm api uv run alembic upgrade head
```

If PostgreSQL is still starting, wait a few seconds and run the migration command
again.

Start the API:

```bash
docker compose up -d api
```

Check the running containers and API:

```bash
docker compose ps
curl http://localhost:8000/health
```

Interactive API docs are available at:

```text
http://localhost:8000/docs
```

To stop the stack without deleting PostgreSQL and Redis volumes:

```bash
docker compose down
```

### Testing

Run the test suite:

```bash
uv run pytest
```

Run linting and type checks:

```bash
uv run ruff check .
uv run mypy app tests
```

### API Overview

- `POST /auth/register` - create a user.
- `POST /auth/login` - login and receive access/refresh tokens.
- `POST /auth/refresh` - rotate refresh token and receive a new token pair.
- `POST /auth/logout` - revoke a refresh token.
- `GET /auth/users/me` - read the current user.
- `GET /api/v1/projects/` - list projects available to the current user.
- `POST /api/v1/projects/` - create a project.
- `GET /api/v1/projects/{project_id}` - read a project.
- `PATCH /api/v1/projects/{project_id}` - update a project.
- `DELETE /api/v1/projects/{project_id}` - delete a project.
- `GET /api/v1/projects/{project_id}/members` - list project members.
- `POST /api/v1/projects/{project_id}/invites/users/{recipient_id}` - invite a user.
- `GET /api/v1/invites` - list current user's invites.
- `PATCH /api/v1/invites/accept/{invite_id}` - accept an invite.
- `PATCH /api/v1/invites/decline/{invite_id}` - decline an invite.
- `POST /api/v1/projects/{project_id}/sprints/` - create a sprint.
- `GET /api/v1/projects/{project_id}/sprints/` - list project sprints.
- `PATCH /api/v1/projects/{project_id}/sprints/{sprint_id}/start` - start a sprint.
- `PATCH /api/v1/projects/{project_id}/sprints/{sprint_id}/close` - close a sprint.
- `POST /api/v1/projects/{project_id}/sprints/{sprint_id}/tasks/` - create a task.
- `GET /api/v1/projects/{project_id}/sprints/{sprint_id}/tasks/` - list sprint tasks.
- `PATCH /api/v1/projects/{project_id}/sprints/{sprint_id}/tasks/{task_id}/take_task` - take a task.
- `PATCH /api/v1/projects/{project_id}/sprints/{sprint_id}/tasks/{task_id}/to_review` - send a task to review.
- `PATCH /api/v1/projects/{project_id}/sprints/{sprint_id}/tasks/{task_id}/accept` - accept reviewed work.
- `PATCH /api/v1/projects/{project_id}/sprints/{sprint_id}/tasks/{task_id}/decline` - decline reviewed work.
