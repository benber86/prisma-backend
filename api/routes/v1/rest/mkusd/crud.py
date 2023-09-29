from aiocache import Cache, cached
from sqlalchemy import Integer, and_, bindparam, select, text

from api.models.common import DecimalTimeSeries, IntegerLabelledSeries, Period
from api.routes.utils.time import apply_period
from database.engine import db
from database.models.common import StableCoinPrice


@cached(ttl=300, cache=Cache.MEMORY)
async def get_price_history(
    chain_id: int, period: Period
) -> list[DecimalTimeSeries]:
    start_timestamp = apply_period(period)
    query = (
        select([StableCoinPrice.price, StableCoinPrice.timestamp])
        .where(
            and_(
                StableCoinPrice.chain_id == chain_id,
                StableCoinPrice.timestamp >= start_timestamp,
            )
        )
        .order_by(StableCoinPrice.timestamp)
    )

    results = await db.fetch_all(query)
    return [
        DecimalTimeSeries(value=result["price"], timestamp=result["timestamp"])
        for result in results
    ]


@cached(ttl=300, cache=Cache.MEMORY)
async def get_price_histogram(
    chain_id: int, bins: int, period: Period
) -> list[IntegerLabelledSeries]:

    start_timestamp = apply_period(period)

    query = text(
        """
        SELECT
            count(*) as bin_count,
            min(price) as bin_min,
            max(price) as bin_max
        FROM
            (
                SELECT
                    width_bucket(price, min_price, max_price, :bins) as bin,
                    price
                FROM
                    mkusd_price,
                    (
                        SELECT
                            min(price) as min_price,
                            max(price) as max_price
                        FROM
                            mkusd_price
                        WHERE
                            chain_id = :chain_id AND
                            timestamp >= :start_timestamp
                    ) as stats
                WHERE
                    chain_id = :chain_id AND
                    timestamp >= :start_timestamp
            ) as binned_data
        GROUP BY
            bin
        ORDER BY
            bin_min;
    """
    )

    query = query.bindparams(
        bindparam("chain_id", value=chain_id, type_=Integer),
        bindparam("bins", value=bins, type_=Integer),
        bindparam("start_timestamp", value=start_timestamp, type_=Integer),
    )

    results = await db.fetch_all(query)

    return [
        IntegerLabelledSeries(
            value=int(result["bin_count"]),
            label=f"[{result['bin_min']}, {result['bin_max']})",
        )
        for result in results
    ]
