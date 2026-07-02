import time

from app.jobs.celery_app import celery_app


@celery_app.task(name="project_hub.demo.add")
def add(x: int, y: int) -> int:
    print(f"Task started: {x} + {y}", flush=True)

    time.sleep(5)

    result = x + y

    print(f"Task finished: result={result}", flush=True)

    return result
