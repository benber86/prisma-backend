import logging

from database.engine import db
from database.models.cvxprisma import CvxPrismaStaking, StakingSnapshot
from database.utils import upsert_query
from services.cvxprisma.utils import get_cvxprisma_snapshot_query_setup
from utils.const import CHAINS
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()

SNAPSHOT_QUERY = """
{
  hourlySnapshots(first:1000 where:{index_gte: %d index_lt: %d}) {
    tokenBalance
    totalSupply
    totalApr
    tvl
    rewardApr {
      apr
      token {
        symbol
      }
    }
  timestamp
  }
}
"""


async def update_snapshots(
    chain: str,
    staking_id: str,
    from_index: int,
    to_index: int | None,
):
    to_index, endpoint = get_cvxprisma_snapshot_query_setup(
        chain, from_index, to_index
    )

    logger.info(
        f"Updating cvxPrisma snapshots from index {from_index} to {to_index}"
    )
    for index in range(from_index, to_index, 1000):
        query = SNAPSHOT_QUERY % (
            index,
            min(to_index + 1, from_index + 1000),
        )
        snapshot_data = await async_grt_query(endpoint=endpoint, query=query)
        if not snapshot_data:
            # reset count to previous value if error
            chain_id = CHAINS[chain]
            indexes = {"chain_id": chain_id, "id": staking_id}
            data = {
                "snapshot_count": from_index,
            }
            query = upsert_query(CvxPrismaStaking, indexes, data)
            await db.execute(query)
            raise Exception(
                f"Did not receive any data from the graph on chain {chain} when querying for staking snapshots"
            )

        for snapshot in snapshot_data["hourlySnapshots"]:

            indexes = {
                "staking_id": staking_id,
                "timestamp": snapshot["timestamp"],
            }
            apr_data = [
                {"apr": apr["apr"], "token": apr["token"]["symbol"]}
                for apr in snapshot["rewardApr"]
            ]
            insert_snapshot_data = {
                "token_balance": snapshot["tokenBalance"],
                "token_supply": snapshot["totalSupply"],
                "tvl": snapshot["tvl"],
                "total_apr": snapshot["totalApr"],
                "apr_breakdown": apr_data,
            }

            query = upsert_query(
                StakingSnapshot, indexes, insert_snapshot_data
            )
            await db.execute(query)
