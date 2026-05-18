## ProjectHub - easy project managing system

ProjectHub is simple project managing app, where you can create a project, sprints and tasks, invite your team and even investors to see work progress!

### Project status

- current status: MVP

### What this means:

- only basic functions included.

### Features

- create a project
- create a sprint
- invite people (admins, workers, just viewers)
- as admin they can create sprints, manage them and tasks
- as workers they can take tasks, send them to review and be in touch with whole team

### Security

- jwt based auth

### Tech stack

- fastapi 0.x
- pydantic 2.x
- sqlalchemy 2.x
- alembic 1.x
- pyjwt 2.x
- bcrypt 5.x
- uvicorn 0.x
- pytest 9.x
- httpx 0.x

### Quick start

with uv:

```bash
    uv run uvicorn app.main:py --reload
```

with pip:

```bash
    uvicorn app.main:py --reload
```
