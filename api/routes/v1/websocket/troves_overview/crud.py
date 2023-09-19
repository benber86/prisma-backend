from sqlalchemy import func, select

from api.routes.v1.websocket.troves_overview.models import TroveManagerDetails
from database.engine import db
from database.models.troves import (
    Collateral,
    TroveManager,
    TroveManagerParameter,
    TroveManagerSnapshot,
)


async def get_trove_manager_details(
    chain_id: int, page: int = 1, items: int = 10
) -> list[TroveManagerDetails]:
    offset = (page - 1) * items

    subquery = (
        select(
            TroveManagerSnapshot.manager_id,
            func.max(TroveManagerSnapshot.block_timestamp).label(
                "latest_timestamp"
            ),
        ).group_by(TroveManagerSnapshot.manager_id)
    ).alias("latest_snapshots")

    query = (
        select(
            Collateral.symbol.label("name"),
            TroveManager.address.label("address"),
            TroveManagerSnapshot.total_collateral_usd.label("tvl"),
            TroveManagerSnapshot.total_debt.label("debt"),
            TroveManagerParameter.max_system_debt.label("debt_cap"),
            TroveManagerSnapshot.collateral_ratio.label("cr"),
            TroveManagerParameter.mcr.label("mcr"),
            TroveManagerParameter.interest_rate.label("rate"),
            Collateral.latest_price.label("price"),
            TroveManagerSnapshot.open_troves.label("open_troves"),
            TroveManagerSnapshot.liquidated_troves.label("liq_troves"),
            TroveManagerSnapshot.closed_troves.label("closed_troves"),
            TroveManagerSnapshot.redeemed_troves.label("red_troves"),
        )
        .join(TroveManager, TroveManager.id == Collateral.manager_id)
        .join(
            TroveManagerSnapshot,
            TroveManagerSnapshot.manager_id == TroveManager.id,
        )
        .join(
            subquery, subquery.c.manager_id == TroveManagerSnapshot.manager_id
        )
        .join(
            TroveManagerParameter,
            TroveManagerParameter.id == TroveManagerSnapshot.parameters_id,
        )
        .where(
            (TroveManager.chain_id == chain_id)
            & (
                TroveManagerSnapshot.block_timestamp
                == subquery.c.latest_timestamp
            )
        )
        .offset(offset)
        .limit(items)
    )

    results = await db.fetch_all(query)
    return [TroveManagerDetails(**result) for result in results]
