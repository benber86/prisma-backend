import asyncio
import logging
import sys

from sqlalchemy import select

from database.engine import db, wrap_dbs
from database.models.common import Chain
from database.models.cvxprisma import CvxPrismaStaking, StakeEvent
from database.utils import upsert_query
from services.celery import celery
from services.cvxprisma.events import update_events
from services.cvxprisma.models import StakingData
from services.cvxprisma.staking import update_staking
from utils.const.chains import ethereum

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


@celery.task
def back_populate_chain(chain: str, chain_id: int):
    asyncio.run(wrap_dbs(sync_from_subgraph)(chain, chain_id))


async def get_staking_data(chain_id: int) -> StakingData | None:
    query = select(
        [
            CvxPrismaStaking.id,
            CvxPrismaStaking.deposit_count,
            CvxPrismaStaking.withdraw_count,
            CvxPrismaStaking.payout_count,
            CvxPrismaStaking.snapshot_count,
        ]
    ).where(CvxPrismaStaking.chain_id == chain_id)
    result = await db.fetch_one(query)
    if result:
        return StakingData(
            id=result["id"],
            withdraw_count=result["withdraw_count"],
            deposit_count=result["deposit_count"],
            payout_count=result["payout_count"],
            snapshot_count=result["snapshot_count"],
        )
    return None


async def sync_from_subgraph(
    chain: str = ethereum.CHAIN_NAME, chain_id: int = ethereum.CHAIN_ID
):
    await db.execute(upsert_query(Chain, {"id": chain_id}, {"name": chain}))
    previous_data = await get_staking_data(chain_id)
    new_data = await update_staking(chain, chain_id)

    if not new_data:
        raise Exception("Failed to retrieve update cues data from the graph")

    if not previous_data:
        raise Exception(
            "Failed to retrieve existing count data from the database"
        )

    if new_data.withdraw_count > previous_data.withdraw_count:
        await update_events(
            chain,
            new_data.id,
            StakeEvent.StakeOperation.withdraw,
            previous_data.withdraw_count,
            new_data.withdraw_count,
        )
    if new_data.deposit_count > previous_data.deposit_count:
        await update_events(
            chain,
            new_data.id,
            StakeEvent.StakeOperation.stake,
            previous_data.deposit_count,
            new_data.deposit_count,
        )
    if new_data.payout_count > previous_data.payout_count:
        pass
        # await update_payouts(chain, new_data.id, previous_data.payout_count, new_data.payout_count)
    if new_data.snapshot_count > previous_data.snapshot_count:
        pass
        # await update_snapshots(chain, new_data.id, previous_data.snapshot_count, new_data.snapshot_count)
