import logging

from api.routes.v1.websocket.models import Channels, Payload
from api.routes.v1.websocket.stability_pool.models import (
    StabilityPoolOperationDetails,
    StabilityPoolOperationType,
    StabilityPoolPayload,
    StabilityPoolSettings,
)
from database.engine import db
from database.models.common import User
from database.models.troves import (
    CollateralWithdrawal,
    StabilityPoolOperation,
    StabilityPoolSnapshot,
)
from database.queries.collateral import get_collateral_id_by_chain_and_address
from database.queries.stability_pool import get_stability_pool_id_by_chain_id
from database.utils import upsert_query
from services.celery import celery
from services.messaging.handler import STABILITY_POOL_UPDATE
from services.messaging.pubsub import publish_message
from services.sync.utils import get_snapshot_query_setup
from utils.const import CHAINS
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()

POOL_SNAPSHOTS_QUERY = """
{
  stabilityPoolSnapshots(first: 1000 where: {index_gte: %d index_lt: %d}) {
    index
    totalDeposited
    totalCollateralWithdrawnUSD
    blockNumber
    blockTimestamp
    transactionHash
  }
}
"""


POOL_OPERATIONS_QUERY = """
{
  stabilityPoolOperations(first: 1000 where: {index_gte: %d index_lt: %d}) {
    user {
      id
      totalDeposited
      totalCollateralGainedUSD
    }
    operation
    index
    stableAmount
    userDeposit
    withdrawnCollateral {
      collateral {
        id
      }
      collateralAmount
      collateralAmountUSD
    }
    blockNumber
    blockTimestamp
    transactionHash
  }
}
"""


def _str_to_enum_type(
    op_type: str,
) -> StabilityPoolOperation.StabilityPoolOperationType:
    op_type_mapping = {
        "stableDeposit": StabilityPoolOperation.StabilityPoolOperationType.stable_deposit,
        "stableWithdrawal": StabilityPoolOperation.StabilityPoolOperationType.stable_withdrawal,
        "collateralWithdrawal": StabilityPoolOperation.StabilityPoolOperationType.collateral_withdrawal,
    }

    if op_type not in op_type_mapping:
        raise Exception(f"Unknown stability pool operation type: {op_type}")

    return op_type_mapping[op_type]


@celery.task
async def update_pool_snapshots(
    chain: str, from_index: int, to_index: int | None
):
    to_index, endpoint = get_snapshot_query_setup(chain, from_index, to_index)
    pool_id = await get_stability_pool_id_by_chain_id(CHAINS[chain])
    logger.info(
        f"Updating pool snapshots from index {from_index} to {to_index}"
    )
    for index in range(from_index, to_index, 1000):
        query = POOL_SNAPSHOTS_QUERY % (
            index,
            min(to_index + 1, from_index + 1000),
        )
        pool_data = await async_grt_query(endpoint=endpoint, query=query)
        if not pool_data:
            raise Exception(
                f"Did not receive any data from the graph on chain {chain} when query for stability pool snapshots {query}"
            )

        for snapshot_data in pool_data["stabilityPoolSnapshots"]:
            indexes = {
                "pool_id": pool_id,
                "index": snapshot_data["index"],
                "block_timestamp": snapshot_data["blockTimestamp"],
            }
            data = {
                "total_deposited": snapshot_data["totalDeposited"],
                "total_collateral_withdrawn_usd": snapshot_data[
                    "totalCollateralWithdrawnUSD"
                ],
                "block_number": snapshot_data["blockNumber"],
                "transaction_hash": snapshot_data["transactionHash"],
            }
            query = upsert_query(StabilityPoolSnapshot, indexes, data)
            await db.execute(query)


@celery.task
async def update_pool_operations(
    chain: str, from_index: int, to_index: int | None
):
    chain_id = CHAINS[chain]
    to_index, endpoint = get_snapshot_query_setup(chain, from_index, to_index)
    pool_id = await get_stability_pool_id_by_chain_id(CHAINS[chain])
    logger.info(
        f"Updating pool operations from index {from_index} to {to_index}"
    )
    for index in range(from_index, to_index, 1000):
        query = POOL_OPERATIONS_QUERY % (
            index,
            min(to_index + 1, from_index + 1000),
        )
        pool_data = await async_grt_query(endpoint=endpoint, query=query)
        if not pool_data:
            raise Exception(
                f"Did not receive any data from the graph on chain {chain} when query for stability pool operations {query}"
            )

        for operations_data in pool_data["stabilityPoolOperations"]:
            # insert user data
            user_index = {"id": operations_data["user"]["id"]}
            user_data = {
                "total_deposited": operations_data["user"]["totalDeposited"],
                "total_collateral_gained_usd": operations_data["user"][
                    "totalCollateralGainedUSD"
                ],
            }
            query = upsert_query(User, user_index, user_data)
            await db.execute(query)

            indexes = {
                "pool_id": pool_id,
                "index": operations_data["index"],
                "user_id": operations_data["user"]["id"],
                "block_timestamp": operations_data["blockTimestamp"],
            }
            data = {
                "operation": _str_to_enum_type(operations_data["operation"]),
                "stable_amount": operations_data["stableAmount"],
                "user_deposit": operations_data["userDeposit"],
                "block_number": operations_data["blockTimestamp"],
                "transaction_hash": operations_data["transactionHash"],
            }
            query = upsert_query(
                StabilityPoolOperation,
                indexes,
                data,
                return_columns=[StabilityPoolOperation.id],
            )
            operation_id = await db.execute(query)
            if not operation_id:
                raise Exception(
                    f"Could not create entry for operation {operations_data['index']}"
                )

            # finally insert collateral withdrawals
            total_withdrawals: float = 0
            for withdrawal in operations_data["withdrawnCollateral"]:
                col_address = withdrawal["collateral"]["id"]
                collateral_id = await get_collateral_id_by_chain_and_address(
                    chain_id, col_address
                )
                if not collateral_id:
                    raise Exception(f"Could not find collateral {col_address}")
                w_indexes = {
                    "collateral_id": collateral_id,
                    "operation_id": operation_id,
                }
                w_data = {
                    "collateral_amount": withdrawal["collateralAmount"],
                    "collateral_amount_usd": withdrawal["collateralAmountUSD"],
                }
                total_withdrawals += float(withdrawal["collateralAmountUSD"])

                query = upsert_query(CollateralWithdrawal, w_indexes, w_data)
                await db.execute(query)

            # push update to fastApi
            operation = StabilityPoolOperationType(
                operations_data["operation"]
            )
            payload = StabilityPoolOperationDetails(
                user=operations_data["user"]["id"],
                operation=operation,
                amount=total_withdrawals
                if operation
                == StabilityPoolOperationType.COLLATERAL_WITHDRAWAL
                else float(operations_data["stableAmount"]),
                hash=operations_data["transactionHash"],
            )
            message = StabilityPoolPayload(
                channel=f"{Channels.troves_overview.value}_{chain_id}",
                subscription=StabilityPoolSettings(chain=chain),
                type=Payload.update,
                payload=[payload],
            )
            await publish_message(STABILITY_POOL_UPDATE, message.json())
