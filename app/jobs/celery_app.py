from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "project_hub",
    broker=settings.celery_broker_url,
    include=[
        "app.jobs.demo"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],

    task_ignore_result=True,

    timezone="UTC",
    enable_utc=True,

    broker_connection_retry_on_startup=True
)