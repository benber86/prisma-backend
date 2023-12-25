import asyncio
import logging
import sys

from database.engine import wrap_dbs
from services.celery import celery
from services.dao.boost import sync_boost_data
from services.dao.incentives import sync_incentive_votes
from services.dao.ownership import sync_ownership_proposals_and_votes

logger = logging.getLogger()

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


@celery.task
def back_populate_ownership_votes(chain: str, chain_id: int):
    asyncio.run(wrap_dbs(sync_ownership_proposals_and_votes)(chain, chain_id))


@celery.task
def back_populate_incentive_votes(chain: str, chain_id: int):
    asyncio.run(wrap_dbs(sync_incentive_votes)(chain, chain_id))


@celery.task
def back_populate_boost_data(chain: str, chain_id: int):
    asyncio.run(wrap_dbs(sync_boost_data)(chain, chain_id))
