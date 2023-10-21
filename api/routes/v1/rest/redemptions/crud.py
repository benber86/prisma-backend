from sqlalchemy import func, select

from api.models.common import GroupBy, Period
from api.routes.utils.time import apply_period
from api.routes.v1.rest.redemptions.models import (
    AggregateRedemption,
    AggregateRedemptionResponse,
)
from database.engine import db
from database.models.troves import (
    Redemption,
    Trove,
    TroveManager,
    TroveSnapshot,
)


async def get_aggregated_stats(
    chain_id: int, period: Period, groupby: GroupBy
) -> AggregateRedemptionResponse:
    start_timestamp = apply_period(period)
    rounded_timestamp = func.date_trunc(
        groupby, func.to_timestamp(Redemption.block_timestamp)
    )

    query = (
        select(
            func.sum(Redemption.actual_debt_amount).label("redeemed"),
            func.count().label("count"),
            func.extract("epoch", rounded_timestamp).label("timestamp"),
        )
        .where(
            (Redemption.block_timestamp >= start_timestamp)
            & (Redemption.chain_id == chain_id)
        )
        .group_by(rounded_timestamp)
        .order_by(rounded_timestamp)
    )

    results = await db.fetch_all(query)
    response = AggregateRedemptionResponse(
        redemptions=[AggregateRedemption(**dict(result)) for result in results]
    )

    return response
