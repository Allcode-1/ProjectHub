FROM python:3.13-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev --no-cache

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2).read()"

CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" ]
