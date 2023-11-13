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
from services.cvxprisma.rewards import update_payouts
from services.cvxprisma.snapshots import update_snapshots
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
def back_populate_cvxprisma(chain: str, chain_id: int):
    asyncio.run(wrap_dbs(sync_cvx_prisma_from_subgraph)(chain, chain_id))


async def get_staking_data(chain_id: int) -> list[StakingData]:
    query = select(
        [
            CvxPrismaStaking.id,
            CvxPrismaStaking.deposit_count,
            CvxPrismaStaking.withdraw_count,
            CvxPrismaStaking.payout_count,
            CvxPrismaStaking.snapshot_count,
        ]
    ).where(CvxPrismaStaking.chain_id == chain_id)
    res = await db.fetch_all(query)
    if res:
        return [
            StakingData(
                id=result["id"],
                withdraw_count=result["withdraw_count"],
                deposit_count=result["deposit_count"],
                payout_count=result["payout_count"],
                snapshot_count=result["snapshot_count"],
            )
            for result in res
        ]
    return []


async def sync_cvx_prisma_from_subgraph(
    chain: str = ethereum.CHAIN_NAME, chain_id: int = ethereum.CHAIN_ID
):
    await db.execute(upsert_query(Chain, {"id": chain_id}, {"name": chain}))
    total_previous_data = await get_staking_data(chain_id)
    total_new_data = await update_staking(chain, chain_id)

    if not total_new_data:
        raise Exception("Failed to retrieve update cues data from the graph")

    for new_data in total_new_data:

        current_contract = new_data.id
        logger.info(f"Updating data for {current_contract}")
        previous_data_list = [
            entry
            for entry in total_previous_data
            if entry.id == current_contract
        ]

        if not previous_data_list:
            logger.warning(
                f"Did not find previous data for contract {current_contract}. Updating from scratch"
            )
            previous_data = None
        else:
            previous_data = previous_data_list[0]
        if (not previous_data) or (
            new_data.withdraw_count > previous_data.withdraw_count
        ):
            await update_events(
                chain,
                new_data.id,
                StakeEvent.StakeOperation.withdraw,
                previous_data.withdraw_count if previous_data else 0,
                new_data.withdraw_count,
            )
        if (not previous_data) or (
            new_data.deposit_count > previous_data.deposit_count
        ):
            await update_events(
                chain,
                new_data.id,
                StakeEvent.StakeOperation.stake,
                previous_data.deposit_count if previous_data else 0,
                new_data.deposit_count,
            )
        if (not previous_data) or (
            new_data.payout_count > previous_data.payout_count
        ):
            await update_payouts(
                chain,
                new_data.id,
                previous_data.payout_count if previous_data else 0,
                new_data.payout_count,
            )
        if (not previous_data) or (
            new_data.snapshot_count > previous_data.snapshot_count
        ):
            await update_snapshots(
                chain,
                new_data.id,
                previous_data.snapshot_count if previous_data else 0,
                new_data.snapshot_count,
            )
