## After Running the Script

If you opened this file, you probably already ran the script. Follow these steps to make your project skeleton work.

### 1. Configure your database settings in `.env`

- Create a database in PGAdmin.
- Put your username, password, and database name into `DATABASE_URL`.
- Do the same for `TEST_DATABASE_URL` if you want to run tests.
- You can skip the JWT settings for now. They are only needed for JWT-based auth.


### 2. Create and apply your first Alembic migration
AFTER creating your SQLAlchemy models in app/models, run:

```bash
uv run alembic revision --autogenerate -m "your message"
uv run alembic upgrade head
```

These commands will push your models into the database.

Done
Now your pet project is ready to go.

Write anything you want there, even ToDo lists.
