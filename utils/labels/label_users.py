import asyncio
import logging

from sqlalchemy import select
from web3 import Web3

from database.engine import db, wrap_dbs
from database.models.common import User
from database.utils import upsert_user
from services.celery import celery
from utils.const import PROVIDERS
from utils.labels.manual import MANUAL_LABELS

logger = logging.getLogger()


async def label_users(chain: str):
    logger.info("Syncing labels for users")
    provider = Web3(PROVIDERS[chain])
    query = select([User.id]).order_by(User.weight)
    results = await db.fetch_all(query)
    for result in results:
        if result.id in MANUAL_LABELS:
            label = MANUAL_LABELS[result.id]
        else:
            label = provider.ens.name(result.id)
        if label:
            await upsert_user(result.id, {"label": label})


@celery.task
def update_labels(chain: str):
    asyncio.run(wrap_dbs(label_users)(chain))
