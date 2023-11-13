from aiocache import Cache, cached
from sqlalchemy import and_, func, select

from api.routes.utils.time import apply_period
from api.routes.v1.rest.revenue.models import (
    PeriodFilterSet,
    RevenueBreakdownResponse,
    RevenueSnapshotModel,
    RevenueSnapshotsResponse,
)
from database.engine import db
from database.models.common import RevenueSnapshot


@cached(ttl=60, cache=Cache.MEMORY)
async def get_snapshots(
    filter_set: PeriodFilterSet, chain_id: int
) -> RevenueSnapshotsResponse:
    start_timestamp = apply_period(filter_set.period)
    query = (
        select(RevenueSnapshot)
        .where(
            and_(
                RevenueSnapshot.timestamp >= start_timestamp,
                RevenueSnapshot.chain_id == chain_id,
            )
        )
        .order_by(RevenueSnapshot.timestamp)
    )

    results = await db.fetch_all(query)

    snapshots = [
        RevenueSnapshotModel(
            unlock_penalty_revenue_usd=result.unlock_penalty_revenue_usd,
            borrowing_fees_revenue_usd=result.borrowing_fees_revenue_usd,
            redemption_fees_revenue_usd=result.redemption_fees_revenue_usd,
            timestamp=result.timestamp,
        )
        for result in results
    ]

    return RevenueSnapshotsResponse(snapshots=snapshots)


@cached(ttl=60, cache=Cache.MEMORY)
async def get_rev_breakdown(chain_id: int) -> RevenueBreakdownResponse:
    query = select(
        [
            func.sum(RevenueSnapshot.unlock_penalty_revenue_usd).label(
                "total_unlock_penalty"
            ),
            func.sum(RevenueSnapshot.borrowing_fees_revenue_usd).label(
                "total_borrowing_fees"
            ),
            func.sum(RevenueSnapshot.redemption_fees_revenue_usd).label(
                "total_redemption_fees"
            ),
        ]
    ).where(RevenueSnapshot.chain_id == chain_id)
    result = await db.fetch_one(query)

    total_unlock_penalty = (
        result["total_unlock_penalty"]
        if result["total_unlock_penalty"] is not None
        else 0
    )
    total_borrowing_fees = (
        result["total_borrowing_fees"]
        if result["total_borrowing_fees"] is not None
        else 0
    )
    total_redemption_fees = (
        result["total_redemption_fees"]
        if result["total_redemption_fees"] is not None
        else 0
    )

    total_revenue = (
        total_unlock_penalty + total_borrowing_fees + total_redemption_fees
    )

    if total_revenue == 0:
        return RevenueBreakdownResponse(
            unlock_penalty=0, borrowing_fees=0, redemption_fees=0
        )

    unlock_penalty_percentage = (total_unlock_penalty / total_revenue) * 100
    borrowing_fees_percentage = (total_borrowing_fees / total_revenue) * 100
    redemption_fees_percentage = (total_redemption_fees / total_revenue) * 100

    return RevenueBreakdownResponse(
        unlock_penalty=unlock_penalty_percentage,
        borrowing_fees=borrowing_fees_percentage,
        redemption_fees=redemption_fees_percentage,
    )
