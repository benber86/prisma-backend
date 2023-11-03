import logging

from database.engine import db
from database.models.common import User
from database.models.cvxprisma import (
    CvxPrismaStaking,
    RewardPaid,
    StakingBalance,
)
from database.utils import insert_ignore_query, upsert_query
from services.cvxprisma.utils import get_cvxprisma_snapshot_query_setup
from utils.const import CHAINS
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()

PAYOUT_QUERY = """
{
  rewardPaids(first:1000 where:{index_gte: %d index_lt: %d}) {
  user {
    id
  }
  index
  token {
    address
    symbol
  }
  amount
  amountUsd
  }
}
"""


async def update_payouts(
    chain: str,
    staking_id: str,
    from_index: int,
    to_index: int | None,
):
    to_index, endpoint = get_cvxprisma_snapshot_query_setup(
        chain, from_index, to_index
    )

    logger.info(
        f"Updating cvxPrisma payouts from index {from_index} to {to_index}"
    )

    for index in range(from_index, to_index, 1000):
        query = PAYOUT_QUERY % (
            index,
            min(to_index + 1, from_index + 1000),
        )
        payout_data = await async_grt_query(endpoint=endpoint, query=query)
        if not payout_data:
            # reset count to previous value if error
            chain_id = CHAINS[chain]
            indexes = {"chain_id": chain_id, "id": staking_id}
            insert_staking_data = {
                "payout_count": from_index,
            }
            query = upsert_query(
                CvxPrismaStaking, indexes, insert_staking_data
            )
            await db.execute(query)
            raise Exception(
                f"Did not receive any data from the graph on chain {chain} when querying for payout events"
            )

        for event in payout_data["rewardPaids"]:
            user_id = event["user"]["id"].lower()
            query = insert_ignore_query(User, {"id": user_id}, {})
            await db.execute(query)

            indexes = {
                "staking_id": staking_id,
                "user_id": event["user"]["id"],
                "index": event["index"],
            }
            insert_payout_data = {
                "amount": event["amount"],
                "amount_usd": event["amountUsd"],
                "token_address": event["token"]["address"],
                "token_symbol": event["token"]["symbol"],
                "block_timestamp": event["blockTimestamp"],
                "block_number": event["blockNumber"],
                "transaction_hash": event["transactionHash"],
            }

            query = upsert_query(RewardPaid, indexes, insert_payout_data)
            await db.execute(query)
