import logging

from database.engine import db
from database.models.common import User
from database.models.cvxprisma import (
    CvxPrismaStaking,
    StakeEvent,
    StakingBalance,
)
from database.utils import insert_ignore_query, upsert_query
from services.cvxprisma.utils import get_cvxprisma_snapshot_query_setup
from utils.const import CHAINS
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()

EVENT_QUERY = """
{
  %s(first:1000 where:{index_gte: %d index_lt: %d}) {
    user {
      id
      stakeSize
    }
  amount
  amountUsd
  index
  blockNumber
  blockTimestamp
  transactionHash
  }
}
"""


async def update_events(
    chain: str,
    staking_id: str,
    event_type: StakeEvent.StakeOperation,
    from_index: int,
    to_index: int | None,
):
    to_index, endpoint = get_cvxprisma_snapshot_query_setup(
        chain, from_index, to_index
    )

    logger.info(
        f"Updating cvxPrisma withdrawals from index {from_index} to {to_index}"
    )
    label = (
        "stakes"
        if event_type == StakeEvent.StakeOperation.stake
        else "withdrawals"
    )
    for index in range(from_index, to_index, 1000):
        query = EVENT_QUERY % (
            label,
            index,
            min(to_index + 1, from_index + 1000),
        )
        event_data = await async_grt_query(endpoint=endpoint, query=query)
        if not event_data:
            # reset count to previous value if error
            chain_id = CHAINS[chain]
            indexes = {"chain_id": chain_id, "id": staking_id}
            key = (
                "deposit_count"
                if event_type == StakeEvent.StakeOperation.stake
                else "withdraw_count"
            )
            insert_staking_data = {
                key: from_index,
            }
            query = upsert_query(
                CvxPrismaStaking, indexes, insert_staking_data
            )
            await db.execute(query)
            raise Exception(
                f"Did not receive any data from the graph on chain {chain} when querying for staking events"
            )

        for event in event_data[label]:
            user_id = event["user"]["id"].lower()
            query = insert_ignore_query(User, {"id": user_id}, {})
            await db.execute(query)

            indexes = {
                "staking_id": staking_id,
                "user_id": event["user"]["id"],
                "index": event["index"],
            }
            insert_event_data = {
                "amount": event["amount"],
                "amount_usd": event["amountUsd"],
                "operation": event_type,
                "block_timestamp": event["blockTimestamp"],
                "block_number": event["blockNumber"],
                "transaction_hash": event["transactionHash"],
            }

            query = upsert_query(StakeEvent, indexes, insert_event_data)
            await db.execute(query)

            indexes = {
                "staking_id": staking_id,
                "user_id": event["user"]["id"],
                "timestamp": event["block_timestamp"],
            }
            insert_balance_data = {"stake_size": event["user"]["stakeSize"]}

            query = upsert_query(StakingBalance, indexes, insert_balance_data)
            await db.execute(query)
