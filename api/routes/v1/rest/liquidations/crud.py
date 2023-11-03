from sqlalchemy import and_, desc, func, select
from web3 import Web3

from api.models.common import Pagination, PaginationReponse
from api.routes.utils.time import apply_period
from api.routes.v1.rest.liquidations.models import (
    AggregateLiquidation,
    AggregateLiquidationResponse,
    FilterSet,
    LiquidationDescription,
    ListLiquidationResponse,
    OrderBy,
    OrderFilter,
)
from database.engine import db
from database.models.troves import (
    Liquidation,
    Trove,
    TroveManager,
    TroveSnapshot,
)


async def get_aggregated_liquidation_stats(
    chain_id: int, manager_id: int, filter_set: FilterSet
) -> AggregateLiquidationResponse:
    start_timestamp = apply_period(filter_set.period)

    subquery = (
        select(
            Liquidation.id,
            Liquidation.liquidated_collateral,
            Liquidation.block_timestamp,
        )
        .join(TroveSnapshot, TroveSnapshot.liquidation_id == Liquidation.id)
        .join(Trove, Trove.id == TroveSnapshot.trove_id)
        .where(
            (Liquidation.block_timestamp >= start_timestamp)
            & (Liquidation.chain_id == chain_id)
            & (Trove.manager_id == manager_id)
        )
        .group_by(Liquidation.id)
    ).alias("grouped_liquidations")

    rounded_timestamp = func.date_trunc(
        filter_set.groupby, func.to_timestamp(subquery.c.block_timestamp)
    )

    query = (
        select(
            func.sum(subquery.c.liquidated_collateral).label("liquidated"),
            func.count().label("count"),
            func.extract("epoch", rounded_timestamp).label("timestamp"),
        )
        .select_from(subquery)
        .group_by(rounded_timestamp)
        .order_by(rounded_timestamp)
    )

    results = await db.fetch_all(query)

    liquidations = [
        AggregateLiquidation(
            liquidated=result["liquidated"],
            count=result["count"],
            timestamp=result["timestamp"],
        )
        for result in results
    ]

    return AggregateLiquidationResponse(liquidations=liquidations)


async def search_liquidations(
    chain_id: int,
    manager_id: int | None,
    pagination: Pagination,
    order: OrderFilter,
) -> ListLiquidationResponse:

    conditions = [Liquidation.chain_id == chain_id]

    if manager_id is not None:
        conditions.append(Trove.manager_id == manager_id)

    base_query = (
        select(Liquidation)
        .outerjoin(
            TroveSnapshot, TroveSnapshot.liquidation_id == Liquidation.id
        )
        .outerjoin(Trove, TroveSnapshot.trove_id == Trove.id)
        .outerjoin(TroveManager, Trove.manager_id == TroveManager.id)
        .where(and_(*conditions))
    )

    if order.trove_filter:
        trove_filter_query = select(Trove.id).where(
            Trove.owner_id.ilike(f"%{order.trove_filter}%")
        )
        base_query = base_query.where(Trove.id.in_(trove_filter_query))

    total_records_query = select(func.count()).select_from(
        base_query.alias("subquery")
    )
    total_records = await db.fetch_val(total_records_query)

    query = base_query.add_columns(
        TroveManager.address.label("vault"),
        func.array_agg(Trove.owner_id).label("troves_affected"),
        func.count(Trove.id).label("troves_affected_count"),
    ).group_by(Liquidation.id, TroveManager.address)

    if order.liquidator_filter:
        query = query.where(
            Liquidation.liquidator_id.ilike(f"%{order.liquidator_filter}%")
        )

    if order.order_by == OrderBy.troves_affected_count.value:
        query = query.order_by(
            desc("troves_affected_count")
            if order.desc
            else "troves_affected_count"
        )
    elif order.order_by == OrderBy.vault.value:
        query = query.order_by(desc("vault") if order.desc else "vault")
    else:
        query = query.order_by(
            desc(getattr(Liquidation, order.order_by))  # type: ignore
            if order.desc
            else getattr(Liquidation, order.order_by)  # type: ignore
        )

    query = query.limit(pagination.items).offset(
        (pagination.page - 1) * pagination.items
    )
    results = await db.fetch_all(query)

    liquidations = [
        LiquidationDescription(
            liquidator=Web3.to_checksum_address(result.liquidator_id),
            vault=Web3.to_checksum_address(result.vault),
            liquidated_debt=float(result.liquidated_debt),
            liquidated_collateral=float(result.liquidated_collateral),
            liquidated_collateral_usd=float(result.liquidated_collateral_usd),
            collateral_gas_compensation=float(result.coll_gas_compensation),
            collateral_gas_compensation_usd=float(
                result.coll_gas_compensation_usd
            ),
            debt_gas_compensation=float(result.debt_gas_compensation),
            troves_affected=[
                Web3.to_checksum_address(trove)
                for trove in result.troves_affected
            ],
            troves_affected_count=result.troves_affected_count,
            transaction=result.transaction_hash,
            timestamp=result.block_timestamp,
        )
        for result in results
    ]

    total_pages = (total_records + pagination.items - 1) // pagination.items

    pagination_response = PaginationReponse(
        total_records=total_records,
        total_pages=total_pages,
        items=pagination.items,
        page=pagination.page,
    )

    return ListLiquidationResponse(
        pagination=pagination_response, liquidations=liquidations
    )
