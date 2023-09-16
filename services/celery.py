import os

from celery import Celery

celery = Celery(
    "Prisma Monitor Jobs",
    backend=os.getenv("CELERY_RESULT_BACKEND"),
    broker=os.getenv("CELERY_BROKER_URL"),
)
