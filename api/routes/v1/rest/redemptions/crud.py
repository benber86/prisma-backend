from sqlalchemy import desc, distinct, func, select
from web3 import Web3

from api.models.common import GroupBy, Pagination, PaginationReponse, Period
from api.routes.utils.time import apply_period
from api.routes.v1.rest.redemptions.models import (
    AggregateRedemption,
    AggregateRedemptionResponse,
    ListRedemptionResponse,
    OrderBy,
    OrderFilter,
    RedemptionDescription,
)
from database.engine import db
from database.models.troves import Redemption, Trove, TroveSnapshot


async def get_aggregated_stats(
    chain_id: int, manager_id: int, period: Period, groupby: GroupBy
) -> AggregateRedemptionResponse:
    start_timestamp = apply_period(period)

    subquery = (
        select(
            Redemption.id,
            Redemption.actual_debt_amount,
            Redemption.block_timestamp,
        )
        .join(TroveSnapshot, TroveSnapshot.redemption_id == Redemption.id)
        .join(Trove, Trove.id == TroveSnapshot.trove_id)
        .where(
            (Redemption.block_timestamp >= start_timestamp)
            & (Redemption.chain_id == chain_id)
            & (Trove.manager_id == manager_id)
        )
        .group_by(Redemption.id)
    ).alias("grouped_redemptions")

    rounded_timestamp = func.date_trunc(
        groupby, func.to_timestamp(subquery.c.block_timestamp)
    )

    query = (
        select(
            func.sum(subquery.c.actual_debt_amount).label("redeemed"),
            func.count().label("count"),
            func.extract("epoch", rounded_timestamp).label("timestamp"),
        )
        .select_from(subquery)
        .group_by(rounded_timestamp)
        .order_by(rounded_timestamp)
    )

    results = await db.fetch_all(query)
    response = AggregateRedemptionResponse(
        redemptions=[AggregateRedemption(**dict(result)) for result in results]
    )

    return response


async def search_redemptions(
    chain_id: int, manager_id: int, pagination: Pagination, order: OrderFilter
) -> ListRedemptionResponse:
    base_query = (
        select(Redemption)
        .outerjoin(TroveSnapshot, TroveSnapshot.redemption_id == Redemption.id)
        .outerjoin(Trove, TroveSnapshot.trove_id == Trove.id)
        .where(
            (Redemption.chain_id == chain_id)
            & (Trove.manager_id == manager_id)
        )
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
        func.array_agg(Trove.owner_id).label("troves_affected"),
        func.count(Trove.id).label("troves_affected_count"),
    ).group_by(Redemption.id)

    if order.redeemer_filter:
        query = query.where(
            Redemption.redeemer_id.ilike(f"%{order.redeemer_filter}%")
        )

    if order.order_by == OrderBy.troves_affected_count.value:
        query = query.order_by(
            desc("troves_affected_count")
            if order.desc
            else "troves_affected_count"
        )
    else:
        query = query.order_by(
            desc(getattr(Redemption, order.order_by))  # type: ignore
            if order.desc
            else getattr(Redemption, order.order_by)  # type: ignore
        )

    query = query.limit(pagination.items).offset(
        (pagination.page - 1) * pagination.items
    )
    results = await db.fetch_all(query)

    redemptions = [
        RedemptionDescription(
            redeemer=Web3.to_checksum_address(result.redeemer_id),
            attempted_debt_amount=float(result.attempted_debt_amount),
            actual_debt_amount=float(result.actual_debt_amount),
            collateral_sent=float(result.collateral_sent),
            collateral_sent_usd=float(result.collateral_sent_usd),
            collateral_sent_to_redeemer=float(
                result.collateral_sent_to_redeemer
            ),
            collateral_sent_to_redeemer_usd=float(
                result.collateral_sent_to_redeemer_usd
            ),
            collateral_fee=float(result.collateral_fee),
            collateral_fee_usd=float(result.collateral_fee_usd),
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

    return ListRedemptionResponse(
        pagination=pagination_response, redemptions=redemptions
    )
