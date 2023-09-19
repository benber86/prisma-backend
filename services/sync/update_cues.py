from sqlalchemy import select

from database.engine import db
from database.models.troves import Collateral, StabilityPool, TroveManager
from services.sync.models import (
    ChainData,
    CollateralData,
    StabilityPoolData,
    TroveManagerData,
)


async def get_data_for_chain(chain_id_value: int) -> ChainData:
    trove_manager_query = select(
        [
            TroveManager.id,
            TroveManager.trove_snapshots_count,
            TroveManager.snapshots_count,
        ]
    ).where(TroveManager.chain_id == chain_id_value)

    collateral_query = select([Collateral.id, Collateral.latest_price]).where(
        Collateral.chain_id == chain_id_value
    )

    stability_pool_query = select(
        [StabilityPool.snapshots_count, StabilityPool.operations_count]
    ).where(StabilityPool.chain_id == chain_id_value)

    async with db.transaction():
        trove_manager_results = await db.fetch_all(trove_manager_query)
        collateral_results = await db.fetch_all(collateral_query)
        stability_pool_result = await db.fetch_one(stability_pool_query)

    trove_manager_data = (
        {
            r["id"]: TroveManagerData(
                trove_snapshots_count=r["trove_snapshots_count"],
                snapshots_count=r["snapshots_count"],
            )
            for r in trove_manager_results
        }
        if trove_manager_results
        else {}
    )

    collateral_data = (
        {
            r["id"]: CollateralData(latest_price=float(r["latest_price"]))
            for r in collateral_results
        }
        if collateral_results
        else {}
    )

    if stability_pool_result:
        stability_pool_data = StabilityPoolData(
            snapshots_count=stability_pool_result["snapshots_count"],
            operations_count=stability_pool_result["operations_count"],
        )
    else:
        stability_pool_data = StabilityPoolData(
            snapshots_count=0, operations_count=0
        )

    result_data = {
        "trove_manager_data": trove_manager_data,
        "collateral_data": collateral_data,
        "stability_pool_data": stability_pool_data,
    }

    return ChainData(**result_data)
