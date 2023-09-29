import os

from celery import Celery

from services.schedules import CELERY_BEAT_SCHEDULE

celery = Celery(
    "Prisma Monitor Jobs",
    backend=os.getenv("CELERY_RESULT_BACKEND"),
    broker=os.getenv("CELERY_BROKER_URL"),
)
celery.conf.update(
    imports=["services.sync.back_populate", "services.prices.populate_mkusd"],
    timezone="UTC",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    beat_schedule=CELERY_BEAT_SCHEDULE,
)
