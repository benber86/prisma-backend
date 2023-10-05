import logging

from web3 import Web3

from api.routes.v1.websocket.models import Channels, Payload
from api.routes.v1.websocket.trove_operations.models import (
    TroveOperation,
    TroveOperationsPayload,
    TroveOperationsSettings,
)
from database.engine import db
from database.models.common import User
from database.models.troves import (
    Liquidation,
    Redemption,
    Trove,
    TroveSnapshot,
)
from database.queries.trove_manager import get_manager_address_by_id_and_chain
from database.utils import insert_ignore_query, upsert_query
from services.celery import celery
from services.messaging.handler import TROVE_OPERATIONS_UPDATE
from services.messaging.pubsub import publish_message
from services.sync.utils import get_snapshot_query_setup
from utils.const import CHAINS
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()


TROVE_SNAPSHOT_QUERY = """
{
  troveSnapshots(first: 1000 where: {manager: "%s" index_gte: %d index_lt: %d}){
    trove {
      owner {
        id
      }
      status
      snapshotsCount
      collateral
      collateralUSD
      collateralRatio
      debt
      stake
      rewardSnapshotDebt
      rewardSnapshotCollateral
    }
    operation
    index
    collateral
    collateralUSD
    collateralRatio
    debt
    stake
    borrowingFee
    liquidation {
      id
      liquidator {
        id
      }
      liquidatedDebt
      liquidatedCollateral
      liquidatedCollateralUSD
      collGasCompensation
      collGasCompensationUSD
      debtGasCompensation
      blockNumber
      blockTimestamp
      transactionHash
    }
    redemption {
      id
      redeemer {
        id
      }
      attemptedDebtAmount
      actualDebtAmount
      collateralSent
      collateralFeeUSD
      collateralSentToRedeemer
      collateralSentToRedeemerUSD
      collateralFee
      collateralFeeUSD
      blockNumber
      blockTimestamp
      transactionHash
    }
    blockNumber
    blockTimestamp
    transactionHash
  }
}
"""


def _str_to_trove_status_enum(status: str) -> Trove.TroveStatus:
    status_mapping = {
        "open": Trove.TroveStatus.open,
        "closedByOwner": Trove.TroveStatus.closed_by_owner,
        "closedByLiquidation": Trove.TroveStatus.closed_by_liquidation,
        "closedByRedemption": Trove.TroveStatus.closed_by_redemption,
    }

    if status not in status_mapping:
        raise Exception(f"Unknown trove status: {status}")

    return status_mapping[status]


def _str_to_trove_operation_enum(
    operation: str,
) -> TroveSnapshot.TroveOperation:
    operation_mapping = {
        "openTrove": TroveSnapshot.TroveOperation.open_trove,
        "closeTrove": TroveSnapshot.TroveOperation.close_trove,
        "adjustTrove": TroveSnapshot.TroveOperation.adjust_trove,
        "applyPendingRewards": TroveSnapshot.TroveOperation.apply_pending_rewards,
        "liquidateInNormalMode": TroveSnapshot.TroveOperation.liquidate_in_normal_mode,
        "liquidateInRecoveryMode": TroveSnapshot.TroveOperation.liquidate_in_recovery_mode,
        "redeemCollateral": TroveSnapshot.TroveOperation.redeem_collateral,
    }

    if operation not in operation_mapping:
        raise Exception(f"Unknown trove operation: {operation}")

    return operation_mapping[operation]


async def _update_liquidation(liquidation: dict) -> str | None:
    if not liquidation:
        return None
    # create user entry
    liquidator_id = liquidation["liquidator"]["id"].lower()
    query = insert_ignore_query(User, {"id": liquidator_id}, {})
    await db.execute(query)

    liq_indexes = {
        "liquidator_id": liquidator_id,
        "block_timestamp": liquidation["blockTimestamp"],
    }
    liq_data = {
        "liquidated_debt": liquidation["liquidatedDebt"],
        "liquidated_collateral": liquidation["liquidatedCollateral"],
        "liquidated_collateral_usd": liquidation["liquidatedCollateralUSD"],
        "coll_gas_compensation": liquidation["collGasCompensation"],
        "coll_gas_compensation_usd": liquidation["collGasCompensationUSD"],
        "debt_gas_compensation": liquidation["debtGasCompensation"],
        "block_number": liquidation["blockNumber"],
        "transaction_hash": liquidation["transactionHash"],
    }
    query = upsert_query(
        Liquidation, liq_indexes, liq_data, return_columns=[Liquidation.id]
    )
    return await db.execute(query)


async def _update_redemption(redemption: dict) -> str | None:
    if not redemption:
        return None
    # create user entry
    redeemer_id = redemption["redeemer"]["id"].lower()
    query = insert_ignore_query(User, {"id": redeemer_id}, {})
    await db.execute(query)

    red_indexes = {
        "redeemer_id": redeemer_id,
        "block_timestamp": redemption["blockTimestamp"],
    }
    red_data = {
        "attempted_debt_amount": redemption["attemptedDebtAmount"],
        "actual_debt_amount": redemption["actualDebtAmount"],
        "collateral_sent": redemption["collateralSent"],
        "collateral_sent_usd": redemption["collateralSentUSD"],
        "collateral_sent_to_redeemer": redemption["collateralSentToRedeemer"],
        "collateral_sent_to_redeemer_usd": redemption[
            "collateralSentToRedeemerUSD"
        ],
        "collateral_fee": redemption["collateralFee"],
        "collateral_fee_usd": redemption["collateralFeeUSD"],
        "block_number": redemption["blockNumber"],
        "transaction_hash": redemption["transactionHash"],
    }
    query = upsert_query(
        Redemption, red_indexes, red_data, return_columns=[Redemption.id]
    )
    return await db.execute(query)


async def _update_trove(manager_id: int, trove: dict) -> str:
    if not trove:
        raise Exception(f"No trove data found for snapshot on {manager_id}")
    # create user entry
    user_id = trove["owner"]["id"].lower()
    query = insert_ignore_query(User, {"id": user_id}, {})
    await db.execute(query)

    trove_indexes = {"manager_id": manager_id, "owner_id": user_id}
    trove_data = {
        "status": _str_to_trove_status_enum(trove["status"]),
        "snapshots_count": trove["snapshotsCount"],
        "collateral": trove["collateral"],
        "collateral_usd": trove["collateralUSD"],
        "debt": trove["debt"],
        "stake": trove["stake"],
        "reward_snapshot_collateral": trove["rewardSnapshotDebt"],
        "reward_snapshot_debt": trove["rewardSnapshotCollateral"],
    }
    query = upsert_query(
        Trove, trove_indexes, trove_data, return_columns=[Trove.id]
    )
    return await db.execute(query)


@celery.task
async def update_trove_snapshots(
    chain: str, manager_id: int, from_index: int, to_index: int | None
):
    chain_id = CHAINS[chain]
    to_index, endpoint = get_snapshot_query_setup(chain, from_index, to_index)
    manager_address = await get_manager_address_by_id_and_chain(
        chain_id, manager_id
    )
    if not manager_address:
        raise Exception(f"Unable to retrieve address of manager {manager_id}")

    logger.info(
        f"Updating trove snapshots from index {from_index} to {to_index} for {manager_address}"
    )
    for index in range(from_index, to_index, 1000):
        query = TROVE_SNAPSHOT_QUERY % (
            manager_address,
            index,
            min(to_index + 1, from_index + 1000),
        )
        snapshot_data = await async_grt_query(endpoint=endpoint, query=query)
        if not snapshot_data:
            logger.error(
                f"Did not receive any data from the graph on chain {chain} when query for trove snapshots {query}"
            )
            return
        for snapshot in snapshot_data["troveSnapshots"]:
            trove_id = await _update_trove(manager_id, snapshot["trove"])

            indexes = {
                "trove_id": trove_id,
                "index": snapshot["index"],
                "block_timestamp": snapshot["blockTimestamp"],
            }

            liquidation_id = await _update_liquidation(snapshot["liquidation"])
            redemption_id = await _update_redemption(snapshot["redemption"])
            data = {
                "operation": _str_to_trove_operation_enum(
                    snapshot["operation"]
                ),
                "collateral": snapshot["collateral"],
                "collateral_usd": snapshot["collateralUSD"],
                "collateral_ratio": snapshot["collateralRatio"],
                "debt": snapshot["debt"],
                "stake": snapshot["stake"],
                "borrowing_fee": snapshot["borrowingFee"],
                "liquidation_id": liquidation_id,
                "redemption_id": redemption_id,
                "block_number": snapshot["blockNumber"],
                "transaction_hash": snapshot["transactionHash"],
            }
            query = upsert_query(TroveSnapshot, indexes, data)
            await db.execute(query)
            # push to fastApi
            settings = TroveOperationsSettings(
                chain=chain, manager=manager_address.lower(), pagination=None
            )
            ops = TroveOperation(
                owner=Web3.to_checksum_address(
                    snapshot["trove"]["owner"]["id"]
                ),
                operation=snapshot["operation"],
                collateral_usd=snapshot["collateralUSD"],
                debt=snapshot["debt"],
                timestamp=snapshot["blockTimestamp"],
                hash=snapshot["transactionHash"],
            )
            payload = TroveOperationsPayload(
                channel=Channels.trove_operations.value,
                subscription=settings,
                type=Payload.update,
                payload=[ops],
            )
            await publish_message(TROVE_OPERATIONS_UPDATE, payload.json())
