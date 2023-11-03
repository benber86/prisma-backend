import os

from celery import Celery
from celery.signals import worker_ready

from services.schedules import CELERY_BEAT_SCHEDULE
from utils.const import CHAINS

celery = Celery(
    "Prisma Monitor Jobs",
    backend=os.getenv("CELERY_RESULT_BACKEND"),
    broker=os.getenv("CELERY_BROKER_URL"),
)
celery.conf.update(
    imports=[
        "services.sync.back_populate",
        "services.cvxprisma.back_populate",
        "services.prices.populate_mkusd",
        "services.prices.mkusd_holders",
        "services.prices.liquidity_depth",
        "services.prices.collateral",
    ],
    timezone="UTC",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    beat_schedule=CELERY_BEAT_SCHEDULE,
)


@worker_ready.connect
def run_task_on_startup(sender, **kwargs):
    print("Worker is ready, executing startup tasks...")
    from services.prices.collateral import get_impact_data
    from services.prices.liquidity_depth import get_depth_data
    from services.prices.mkusd_holders import get_holder_data

    for chain in CHAINS.keys():
        get_holder_data.apply_async(args=(chain,))
        get_depth_data.apply_async(args=(chain,))
        get_impact_data.apply_async(args=(chain,))
