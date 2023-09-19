import logging
from decimal import Decimal

from database.engine import db
from database.models.troves import TroveManagerParameter, TroveManagerSnapshot
from database.queries.trove_manager import get_manager_address_by_id_and_chain
from database.utils import upsert_query
from services.sync.utils import get_snapshot_query_setup
from utils.const import CHAINS
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()


TROVE_MANAGER_SNAPSHOT_QUERY = """
{
  troveManagerSnapshots(first: 1000 where: {manager: "%s" index_gte: %d index_lt: %d}){
    index
    collateralPrice
    rate
    borrowingFee
    totalDebt
    totalCollateralUSD
    totalCollateral
    totalStakes
    collateralRatio

    totalBorrowingFeesPaid
    totalRedemptionFeesPaid
    totalRedemptionFeesPaidUSD

    totalCollateralRedistributed
    totalCollateralRedistributedUSD
    totalDebtRedistributed

    openTroves
    totalTrovesOpened
    liquidatedTroves
    totalTrovesLiquidated
    redeemedTroves
    totalTrovesRedeemed
    closedTroves
    totalTrovesClosed
    totalTroves

    parameters {
      id
      minuteDecayFactor
      redemptionFeeFloor
      borrowingFeeFloor
      maxBorrowingFee
      maxSystemDebt
      maxRedemptionFee
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


async def _update_parameters(
    manager_id: int, parameters: dict | None
) -> str | None:
    if parameters:
        parameter_indexes = {
            "manager_id": manager_id,
            "block_timestamp": parameters["blockTimestamp"],
        }
        parameter_data = {
            "id": parameters["id"],
            "minute_decay_factor": Decimal(parameters["minuteDecayFactor"])
            / 10**18,
            "redemption_fee_floor": Decimal(parameters["redemptionFeeFloor"])
            / 10**18,
            "borrowing_fee_floor": Decimal(parameters["borrowingFeeFloor"])
            / 10**18,
            "max_redemption_fee": Decimal(parameters["maxRedemptionFee"])
            / 10**18,
            "max_borrowing_fee": Decimal(parameters["maxBorrowingFee"])
            / 10**18,
            "max_system_debt": Decimal(parameters["maxSystemDebt"]) / 10**18,
            "block_number": parameters["blockTimestamp"],
            "transaction_hash": parameters["transactionHash"],
        }
        query = upsert_query(
            TroveManagerParameter,
            parameter_indexes,
            parameter_data,
            return_columns=[TroveManagerParameter.id],
        )
        return await db.execute(query)
    return None


async def update_manager_snapshots(
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
        f"Updating trove manager snapshots from index {from_index} to {to_index} for {manager_address}"
    )
    for index in range(from_index, to_index, 1000):
        query = TROVE_MANAGER_SNAPSHOT_QUERY % (
            manager_address,
            index,
            min(to_index + 1, from_index + 1000),
        )
        snapshot_data = await async_grt_query(endpoint=endpoint, query=query)
        if not snapshot_data:
            raise Exception(
                f"Did not receive any data from the graph on chain {chain} when query for trove manager snapshots {query}"
            )
        for snapshot in snapshot_data["troveManagerSnapshots"]:
            parameters_id = await _update_parameters(
                manager_id, snapshot["parameters"]
            )

            indexes = {
                "manager_id": manager_id,
                "index": snapshot["index"],
                "block_timestamp": snapshot["blockTimestamp"],
            }

            data = {
                "collateral_price": snapshot["collateralPrice"],
                "rate": snapshot["rate"],
                "borrowing_fee": snapshot["borrowingFee"],
                "total_collateral": snapshot["totalCollateral"],
                "total_collateral_usd": snapshot["totalCollateralUSD"],
                "total_debt": snapshot["totalDebt"],
                "collateral_ratio": snapshot["collateralRatio"],
                "total_stakes": snapshot["totalStakes"],
                "total_borrowing_fees_paid": snapshot[
                    "totalBorrowingFeesPaid"
                ],
                "total_redemption_fees_paid": snapshot[
                    "totalRedemptionFeesPaid"
                ],
                "total_redemption_fees_paid_usd": snapshot[
                    "totalRedemptionFeesPaidUSD"
                ],
                "total_collateral_redistributed": snapshot[
                    "totalCollateralRedistributed"
                ],
                "total_collateral_redistributed_usd": snapshot[
                    "totalCollateralRedistributedUSD"
                ],
                "total_debt_redistributed": snapshot["totalDebtRedistributed"],
                "open_troves": snapshot["openTroves"],
                "total_troves_opened": snapshot["totalTrovesOpened"],
                "liquidated_troves": snapshot["liquidatedTroves"],
                "total_troves_liquidated": snapshot["totalTrovesLiquidated"],
                "redeemed_troves": snapshot["redeemedTroves"],
                "total_troves_redeemed": snapshot["totalTrovesRedeemed"],
                "closed_troves": snapshot["closedTroves"],
                "total_troves_closed": snapshot["totalTrovesClosed"],
                "total_troves": snapshot["totalTroves"],
                "parameters_id": parameters_id,
                "block_number": snapshot["blockNumber"],
                "transaction_hash": snapshot["transactionHash"],
            }
            query = upsert_query(TroveManagerSnapshot, indexes, data)
            await db.execute(query)
