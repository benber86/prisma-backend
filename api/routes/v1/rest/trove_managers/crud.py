import aiocache
import pandas as pd
from aiocache import Cache, cached
from sqlalchemy import distinct, func, select

from api.models.common import DecimalTimeSeries, Period
from api.routes.utils.time import SECONDS_IN_DAY, apply_period
from api.routes.v1.rest.trove_managers.models import (
    HistoricalCollateralRatioResponse,
    HistoricalOpenedTroves,
    HistoricalOpenedTrovesResponse,
    HistoricalTroveManagerCR,
)
from database.engine import db
from database.models.troves import (
    Collateral,
    TroveManager,
    TroveManagerSnapshot,
)

cache = Cache(Cache.MEMORY)


async def get_historical_collateral_ratios(
    chain_id: int, period: Period
) -> HistoricalCollateralRatioResponse:
    start_timestamp = apply_period(period)
    rounded_timestamp = (
        func.floor(TroveManagerSnapshot.block_timestamp / SECONDS_IN_DAY)
        * SECONDS_IN_DAY
    )

    subquery = (
        select(
            Collateral.name,
            rounded_timestamp.label("rounded_date"),
            func.avg(TroveManagerSnapshot.collateral_ratio).label(
                "avg_collateral_ratio"
            ),
        )
        .join(
            Collateral,
            Collateral.manager_id == TroveManagerSnapshot.manager_id,
        )
        .join(TroveManager, TroveManager.id == TroveManagerSnapshot.manager_id)
        .group_by(Collateral.name, rounded_timestamp)
        .filter(
            (TroveManagerSnapshot.block_timestamp >= start_timestamp)
            & (TroveManager.chain_id == chain_id)
            & (TroveManagerSnapshot.total_collateral_usd.isnot(None))
            & (TroveManagerSnapshot.total_debt.isnot(None))
        )
        .order_by(rounded_timestamp)
    ).alias("average_collaterals")

    results = await db.fetch_all(subquery)

    markets_data: dict[str, list[DecimalTimeSeries]] = {}
    for r in results:
        if r.name not in markets_data:
            markets_data[r.name] = []
        if float(r.avg_collateral_ratio) == 0:
            continue
        data_point = DecimalTimeSeries(
            value=float(r.avg_collateral_ratio), timestamp=r.rounded_date
        )
        markets_data[r.name].append(data_point)

    formatted_data = [
        HistoricalTroveManagerCR(trove=market, data=data)
        for market, data in markets_data.items()
    ]

    return HistoricalCollateralRatioResponse(troves=formatted_data)


async def get_global_collateral_ratio(
    chain_id: int, period: Period
) -> HistoricalTroveManagerCR:
    start_timestamp = apply_period(period)
    rounded_timestamp = (
        func.floor(TroveManagerSnapshot.block_timestamp / SECONDS_IN_DAY)
        * SECONDS_IN_DAY
    )

    cte_manager_count = (
        select(
            rounded_timestamp.label("rounded_date"),
            func.count(distinct(TroveManagerSnapshot.manager_id)).label(
                "manager_count"
            ),
        )
        .join(TroveManager, TroveManager.id == TroveManagerSnapshot.manager_id)
        .filter(TroveManager.chain_id == chain_id)
        .group_by(rounded_timestamp)
        .cte(name="cte_manager_count")
    )

    cte_aggregate = (
        select(
            rounded_timestamp.label("rounded_date"),
            func.sum(TroveManagerSnapshot.total_collateral_usd).label(
                "sum_collateral_usd"
            ),
            func.sum(TroveManagerSnapshot.total_debt).label("sum_debt"),
        )
        .join(TroveManager, TroveManager.id == TroveManagerSnapshot.manager_id)
        .filter(
            (TroveManager.chain_id == chain_id)
            & (TroveManagerSnapshot.block_timestamp >= start_timestamp)
        )
        .group_by(rounded_timestamp)
        .cte(name="cte_aggregate")
    )

    total_managers = await db.fetch_val(
        select(func.count(distinct(TroveManager.id))).where(
            TroveManager.chain_id == chain_id
        )
    )

    final_query = (
        select(
            cte_aggregate.c.rounded_date,
            cte_aggregate.c.sum_collateral_usd,
            cte_aggregate.c.sum_debt,
        )
        .join(
            cte_manager_count,
            cte_manager_count.c.rounded_date == cte_aggregate.c.rounded_date,
        )
        .where(cte_manager_count.c.manager_count == total_managers)
        .order_by(cte_aggregate.c.rounded_date.asc())
    )

    results = await db.fetch_all(final_query)

    data_points = [
        DecimalTimeSeries(
            value=float(row["sum_collateral_usd"] / row["sum_debt"]),
            timestamp=row["rounded_date"],
        )
        for row in results
        if row["sum_debt"] != 0 and row["sum_collateral_usd"] != 0
    ]

    return HistoricalTroveManagerCR(trove="global", data=data_points)


@cached(ttl=300, cache=cache)
async def get_open_troves_overview(
    chain_id: int, period: Period
) -> HistoricalOpenedTrovesResponse:
    start_timestamp = apply_period(period)
    rounded_timestamp = (
        func.floor(TroveManagerSnapshot.block_timestamp / SECONDS_IN_DAY)
        * SECONDS_IN_DAY
    )

    query = (
        select(
            Collateral.name,
            rounded_timestamp.label("rounded_date"),
            func.max(TroveManagerSnapshot.open_troves).label(
                "max_open_troves"
            ),
        )
        .join(TroveManager, TroveManager.id == TroveManagerSnapshot.manager_id)
        .join(
            Collateral, Collateral.manager_id == TroveManager.id
        )  # Corrected join here
        .filter(
            (TroveManager.chain_id == chain_id)
            & (TroveManagerSnapshot.block_timestamp >= start_timestamp)
        )
        .group_by(Collateral.name, rounded_timestamp)
    )

    results = await db.fetch_all(query)

    results_dict = [dict(row) for row in results]

    df = pd.DataFrame(results_dict)
    df_pivot = df.pivot(
        index="rounded_date", columns="name", values="max_open_troves"
    )
    df_pivot.ffill(inplace=True)

    data_dict = df_pivot.to_dict(orient="dict")

    trove_data_list = [
        HistoricalOpenedTroves(
            trove=trove_name,
            data=[
                DecimalTimeSeries(timestamp=date, value=value)
                for date, value in trove_data.items()
                if value != 0
            ],
        )
        for trove_name, trove_data in data_dict.items()
    ]

    return HistoricalOpenedTrovesResponse(troves=trove_data_list)
