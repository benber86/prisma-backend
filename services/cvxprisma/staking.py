import logging

from database.engine import db
from database.models.cvxprisma import CvxPrismaStaking
from database.utils import upsert_query
from services.cvxprisma.models import StakingData
from utils.const import CVXPRISMA_SUBGRAPHS
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()

ENTITY_QUERY = """
{
  stakingContracts {
    id
    tvl
    tokenBalance
    depositCount
    withdrawCount
    payoutCount
    snapshotCount
  }
}
"""


async def update_staking(
    chain: str, chain_id: int
) -> list[StakingData] | None:
    endpoint = CVXPRISMA_SUBGRAPHS[chain]
    entity_data = await async_grt_query(endpoint=endpoint, query=ENTITY_QUERY)
    if not entity_data:
        logger.error(
            f"Did not receive any data from the cvxPrisma graph on chain {chain} when querying for base entities"
        )
        return None
    res: list[StakingData] = []
    for contract in entity_data["stakingContracts"]:
        indexes = {"chain_id": chain_id, "id": contract["id"]}
        data = {
            "tvl": contract["tvl"],
            "token_balance": contract["tokenBalance"],
            "deposit_count": contract["depositCount"],
            "withdraw_count": contract["withdrawCount"],
            "payout_count": contract["payoutCount"],
            "snapshot_count": contract["snapshotCount"],
        }
        query = upsert_query(CvxPrismaStaking, indexes, data)
        await db.execute(query)

        res.append(
            StakingData(
                id=contract["id"],
                deposit_count=contract["depositCount"],
                withdraw_count=contract["withdrawCount"],
                payout_count=contract["payoutCount"],
                snapshot_count=contract["snapshotCount"],
            )
        )
    return res
