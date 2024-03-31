from sqlalchemy import String, func, select

from api.routes.v1.websocket.troves_overview.models import TroveManagerDetails
from database.engine import db
from database.models.troves import (
    Collateral,
    TroveManager,
    TroveManagerParameter,
    TroveManagerSnapshot,
)


async def get_trove_manager_details(
    chain_id: int,
) -> list[TroveManagerDetails]:

    unique_symbol = func.concat(
        Collateral.symbol,
        func.cast(" (", String),
        func.substr(func.cast(TroveManager.address, String), 1, 6),
        func.cast(")", String),
    ).label("unique_symbol")

    query = (
        select(
            unique_symbol.label("name"),
            TroveManager.address.label("address"),
            Collateral.address.label("collateral"),
            TroveManagerSnapshot.total_collateral_usd.label("tvl"),
            TroveManagerSnapshot.total_debt.label("debt"),
            TroveManagerParameter.max_system_debt.label("debt_cap"),
            func.coalesce(TroveManagerSnapshot.collateral_ratio, 0).label(
                "cr"
            ),
            TroveManagerParameter.mcr.label("mcr"),
            TroveManagerParameter.interest_rate.label("rate"),
            Collateral.latest_price.label("price"),
            TroveManagerSnapshot.open_troves.label("open_troves"),
            TroveManagerSnapshot.liquidated_troves.label("liq_troves"),
            TroveManagerSnapshot.closed_troves.label("closed_troves"),
            TroveManagerSnapshot.redeemed_troves.label("red_troves"),
        )
        .join(TroveManager, TroveManager.id == TroveManagerSnapshot.manager_id)
        .join(Collateral, Collateral.id == TroveManager.collateral_id)
        .join(
            TroveManagerParameter,
            TroveManagerParameter.id == TroveManagerSnapshot.parameters_id,
        )
        .where(TroveManager.chain_id == chain_id)
        .distinct(TroveManager.id)
        .order_by(
            TroveManager.id,
            TroveManagerSnapshot.block_timestamp.desc(),
            TroveManagerSnapshot.created_at.desc(),
        )
    )

    results = await db.fetch_all(query)
    return [TroveManagerDetails(**result) for result in results]
