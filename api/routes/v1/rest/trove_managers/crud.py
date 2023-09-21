import pandas as pd
from aiocache import Cache, cached
from sqlalchemy import and_, desc, distinct, func, select

from api.models.common import DecimalTimeSeries, Period
from api.routes.utils.time import SECONDS_IN_DAY, apply_period
from api.routes.v1.rest.trove_managers.models import (
    CollateralRatioDecilesData,
    CollateralRatioDistributionResponse,
    HistoricalCollateralRatioResponse,
    HistoricalOpenedTroves,
    HistoricalOpenedTrovesResponse,
    HistoricalTroveManagerCR,
)
from database.engine import db
from database.models.troves import (
    Collateral,
    Trove,
    TroveManager,
    TroveManagerSnapshot,
    TroveSnapshot,
)


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


@cached(ttl=300, cache=Cache.MEMORY)
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


@cached(ttl=300, cache=Cache.MEMORY)
async def get_health_overview(
    chain_id: int,
) -> CollateralRatioDistributionResponse:

    open_troves = (
        select([Trove.id.label("trove_id")])
        .join(TroveManager, Trove.manager_id == TroveManager.id)
        .where(
            (Trove.status == Trove.TroveStatus.open)
            & (TroveManager.chain_id == chain_id)
        )
        .alias()
    )

    latest_trove_snapshots = (
        select(
            [
                TroveSnapshot.trove_id,
                func.max(TroveSnapshot.block_timestamp).label(
                    "latest_timestamp"
                ),
            ]
        )
        .where(TroveSnapshot.trove_id.in_(open_troves))
        .group_by(TroveSnapshot.trove_id)
        .alias()
    )

    last_manager_snapshots = (
        select(
            [
                TroveManagerSnapshot.manager_id,
                TroveManagerSnapshot.collateral_price,
            ]
        )
        .order_by(
            TroveManagerSnapshot.manager_id,
            desc(TroveManagerSnapshot.block_timestamp),
            desc(TroveManagerSnapshot.id),
        )
        .distinct(TroveManagerSnapshot.manager_id)
        .alias()
    )

    trove_data_query = (
        select(
            [
                TroveSnapshot.trove_id,
                TroveSnapshot.debt,
                (
                    TroveSnapshot.collateral
                    * last_manager_snapshots.c.collateral_price
                ).label("collateral_value"),
                (
                    (
                        TroveSnapshot.collateral
                        * last_manager_snapshots.c.collateral_price
                    )
                    / TroveSnapshot.debt
                ).label("collateral_ratio"),
            ]
        )
        .join(
            latest_trove_snapshots,
            and_(
                TroveSnapshot.trove_id == latest_trove_snapshots.c.trove_id,
                TroveSnapshot.block_timestamp
                == latest_trove_snapshots.c.latest_timestamp,
            ),
        )
        .join(Trove, Trove.id == TroveSnapshot.trove_id)
        .join(
            last_manager_snapshots,
            Trove.manager_id == last_manager_snapshots.c.manager_id,
        )
        .where(Trove.status == Trove.TroveStatus.open)
    )

    trove_data = await db.fetch_all(trove_data_query)
    trove_data_dict = [dict(row) for row in trove_data]

    df = pd.DataFrame(trove_data_dict)
    df = df.applymap(float)
    df["collateral_decile"], bins = pd.qcut(
        df["collateral_ratio"], 10, retbins=True, labels=False
    )
    labels = [
        f"[{round(bins[i] * 100, 2)}% - {round(bins[i + 1] * 100, 2)}%)"
        for i in range(10)
    ]
    df["decile"] = df["collateral_decile"].map(lambda x: labels[x])
    debt_by_decile = df.groupby("decile")["debt"].sum().reset_index()
    deciles_data = [
        CollateralRatioDecilesData(label=row["decile"], data=row["debt"])
        for row in debt_by_decile.to_dict(orient="records")
    ]

    return CollateralRatioDistributionResponse(deciles=deciles_data)
