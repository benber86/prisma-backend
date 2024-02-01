from datetime import datetime

import numpy as np
import pandas as pd
from aiocache import Cache, cached
from sqlalchemy import String, and_, case, desc, distinct, func, select

from api.models.common import (
    DecimalLabelledSeries,
    DecimalTimeSeries,
    Denomination,
    Period,
)
from api.routes.utils.histogram import make_histogram
from api.routes.utils.time import SECONDS_IN_DAY, apply_period
from api.routes.v1.rest.trove_managers.models import (
    CollateralRatioDecilesData,
    CollateralRatioDistributionResponse,
    CollateralVsDebt,
    DistributionResponse,
    HistoricalOpenedTroves,
    HistoricalOpenedTrovesResponse,
    HistoricalTroveManagerData,
    HistoricalTroveOverviewResponse,
    LargePositionsResponse,
    SingleVaultCollateralRatioResponse,
    SingleVaultEvents,
    SingleVaultTroveCountResponse,
)
from database.engine import db
from database.models.common import User
from database.models.troves import (
    Collateral,
    Trove,
    TroveManager,
    TroveManagerSnapshot,
    TroveSnapshot,
)


async def get_historical_collateral_ratios(
    chain_id: int, period: Period
) -> HistoricalTroveOverviewResponse:
    start_timestamp = apply_period(period)
    rounded_timestamp = (
        func.floor(TroveManagerSnapshot.block_timestamp / SECONDS_IN_DAY)
        * SECONDS_IN_DAY
    )
    unique_symbol = func.concat(
        Collateral.symbol,
        func.cast(" (", String),
        func.substr(func.cast(TroveManager.address, String), 1, 6),
        func.cast(")", String),
    ).label("unique_symbol")

    subquery = (
        select(
            unique_symbol,
            rounded_timestamp.label("rounded_date"),
            func.max(TroveManagerSnapshot.collateral_ratio).label(
                "max_collateral_ratio"
            ),
        )
        .join(TroveManager, TroveManager.id == TroveManagerSnapshot.manager_id)
        .join(Collateral, Collateral.id == TroveManager.collateral_id)
        .group_by(unique_symbol, rounded_timestamp)
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
        symbol = r.unique_symbol
        if symbol not in markets_data:
            markets_data[symbol] = []
        if float(r.max_collateral_ratio) == 0:
            continue
        data_point = DecimalTimeSeries(
            value=float(r.max_collateral_ratio), timestamp=r.rounded_date
        )
        markets_data[symbol].append(data_point)

    formatted_data = [
        HistoricalTroveManagerData(manager=market, data=data)
        for market, data in markets_data.items()
    ]

    return HistoricalTroveOverviewResponse(managers=formatted_data)


@cached(ttl=300, cache=Cache.MEMORY)
async def get_global_collateral_ratio(
    chain_id: int, period: Period
) -> HistoricalTroveManagerData:

    start_timestamp = apply_period(period)
    rounded_timestamp = (
        func.floor(TroveManagerSnapshot.block_timestamp / SECONDS_IN_DAY)
        * SECONDS_IN_DAY
    )

    subquery = (
        select(
            TroveManager.address,
            rounded_timestamp.label("rounded_date"),
            func.avg(TroveManagerSnapshot.total_collateral_usd).label(
                "avg_collateral_usd"
            ),
            func.avg(TroveManagerSnapshot.total_debt).label("avg_debt"),
        )
        .join(TroveManager, TroveManager.id == TroveManagerSnapshot.manager_id)
        .filter(
            (TroveManager.chain_id == chain_id)
            & (TroveManagerSnapshot.block_timestamp >= start_timestamp)
        )
        .group_by(TroveManager.address, rounded_timestamp)
        .order_by(rounded_timestamp)
    )

    results = await db.fetch_all(subquery)

    df = pd.DataFrame([dict(row) for row in results])

    df_collateral = df.pivot(
        index="rounded_date", columns="address", values="avg_collateral_usd"
    )
    df_debt = df.pivot(
        index="rounded_date", columns="address", values="avg_debt"
    )

    df_collateral.ffill(inplace=True)
    df_debt.ffill(inplace=True)

    df_collateral.fillna(0, inplace=True)
    df_debt.fillna(0, inplace=True)

    global_collateral = df_collateral.sum(axis=1)
    global_debt = df_debt.sum(axis=1)
    global_collateral_ratio = (global_collateral / global_debt).astype(float)

    data_points = [
        DecimalTimeSeries(value=float(ratio), timestamp=index)
        for index, ratio in global_collateral_ratio.items()
        if not np.isnan(ratio) and ratio != 0
    ]

    return HistoricalTroveManagerData(manager="global", data=data_points)


@cached(ttl=300, cache=Cache.MEMORY)
async def get_open_troves_overview(
    chain_id: int, period: Period
) -> HistoricalOpenedTrovesResponse:
    start_timestamp = apply_period(period)
    rounded_timestamp = (
        func.floor(TroveManagerSnapshot.block_timestamp / SECONDS_IN_DAY)
        * SECONDS_IN_DAY
    )
    unique_symbol = func.concat(
        Collateral.symbol,
        func.cast(" (", String),
        func.substr(func.cast(TroveManager.address, String), 1, 6),
        func.cast(")", String),
    ).label("unique_symbol")

    query = (
        select(
            unique_symbol,
            rounded_timestamp.label("rounded_date"),
            func.max(TroveManagerSnapshot.open_troves).label(
                "max_open_troves"
            ),
        )
        .join(TroveManager, TroveManager.id == TroveManagerSnapshot.manager_id)
        .join(Collateral, Collateral.id == TroveManager.collateral_id)
        .filter(
            (TroveManager.chain_id == chain_id)
            & (TroveManagerSnapshot.block_timestamp >= start_timestamp)
        )
        .group_by(unique_symbol, rounded_timestamp)
    )

    results = await db.fetch_all(query)

    results_dict = [dict(row) for row in results]

    df = pd.DataFrame(results_dict)
    print(df)
    df_pivot = df.pivot(
        index="rounded_date", columns="unique_symbol", values="max_open_troves"
    )
    df_pivot.ffill(inplace=True)

    data_dict = df_pivot.to_dict(orient="dict")

    trove_data_list = [
        HistoricalOpenedTroves(
            manager=trove_name,
            data=[
                DecimalTimeSeries(timestamp=date, value=value if value else 0)
                for date, value in trove_data.items()
            ],
        )
        for trove_name, trove_data in data_dict.items()
    ]

    return HistoricalOpenedTrovesResponse(managers=trove_data_list)


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
        .where(and_(TroveSnapshot.trove_id.in_(open_troves), Trove.debt != 0))
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
                case(
                    [(TroveSnapshot.debt == 0, 0)],
                    else_=(
                        TroveSnapshot.collateral
                        * last_manager_snapshots.c.collateral_price
                    )
                    / TroveSnapshot.debt,
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
        f"[{round(bins[i] * 100)}% - {round(bins[i + 1] * 100)}%)"
        for i in range(10)
    ]
    df["decile"] = df["collateral_decile"].map(lambda x: labels[x])
    debt_by_decile = df.groupby("decile")["debt"].sum().reset_index()
    deciles_data = [
        CollateralRatioDecilesData(label=row["decile"], data=row["debt"])
        for row in debt_by_decile.to_dict(orient="records")
    ]

    return CollateralRatioDistributionResponse(deciles=deciles_data)


@cached(ttl=300, cache=Cache.MEMORY)
async def get_historical_collateral_usd(
    chain_id: int, period: Period
) -> HistoricalTroveOverviewResponse:
    start_timestamp = apply_period(period)
    rounded_timestamp = (
        func.floor(TroveManagerSnapshot.block_timestamp / SECONDS_IN_DAY)
        * SECONDS_IN_DAY
    )

    subquery = (
        select(
            Collateral.symbol,
            rounded_timestamp.label("rounded_date"),
            func.max(TroveManagerSnapshot.total_collateral_usd).label(
                "max_collateral_usd"
            ),
        )
        .join(TroveManager, TroveManager.id == TroveManagerSnapshot.manager_id)
        # .join(Collateral, Collateral.manager_id == TroveManager.id)
        .group_by(Collateral.symbol, rounded_timestamp)
        .filter(
            (TroveManager.chain_id == chain_id)
            & (TroveManagerSnapshot.block_timestamp >= start_timestamp)
            & (TroveManagerSnapshot.total_collateral_usd.isnot(None))
        )
        .order_by(rounded_timestamp)
    ).alias("average_collaterals")

    results = await db.fetch_all(subquery)
    trove_data_dict = [dict(row) for row in results]

    df = pd.DataFrame(trove_data_dict)
    df_pivot = df.pivot(
        index="rounded_date", columns="symbol", values="max_collateral_usd"
    )
    df_pivot.ffill(inplace=True)
    df_pivot.fillna(0, inplace=True)
    troves_data = []
    for col in df_pivot.columns:
        time_series_data = [
            DecimalTimeSeries(value=row[col], timestamp=index)
            for index, row in df_pivot.iterrows()
        ]
        troves_data.append(
            HistoricalTroveManagerData(manager=col, data=time_series_data)
        )

    return HistoricalTroveOverviewResponse(managers=troves_data)


async def get_collateral_histogram(manager_id: int) -> DistributionResponse:
    query = (
        select([Trove.collateral_usd])
        .where(Trove.manager_id == manager_id)
        .where(Trove.status == Trove.TroveStatus.open)
    )
    results = await db.fetch_all(query)
    series = pd.Series([float(r[0]) for r in results])
    distrib = make_histogram(series)
    return DistributionResponse(distribution=distrib)


async def get_debt_histogram(manager_id: int) -> DistributionResponse:
    query = (
        select([Trove.debt])
        .where(Trove.manager_id == manager_id)
        .where(Trove.status == Trove.TroveStatus.open)
    )
    results = await db.fetch_all(query)
    series = pd.Series([float(r[0]) for r in results])
    distrib = make_histogram(series)
    return DistributionResponse(distribution=distrib)


@cached(ttl=300, cache=Cache.MEMORY)
async def get_large_positions(
    manager_id: int, top_values: int, denomination: CollateralVsDebt
) -> LargePositionsResponse:

    if denomination.unit == Denomination.collateral.value:
        column = Trove.collateral_usd
    else:
        column = Trove.debt

    top_troves_query = (
        select([User.id.label("label"), column.label("value")])
        .join(Trove, User.id == Trove.owner_id)
        .where(Trove.manager_id == manager_id)
        .where(Trove.status == Trove.TroveStatus.open)
        .order_by(desc(column))
        .limit(top_values)
    )
    top_troves = await db.fetch_all(top_troves_query)

    subquery = (
        select([column])
        .where(Trove.manager_id == manager_id)
        .where(Trove.status == Trove.TroveStatus.open)
        .order_by(desc(column))
        .limit(top_values)
        .alias()
    )

    remaining_troves_sum_query = (
        select([func.sum(column)])
        .where(Trove.manager_id == manager_id)
        .where(Trove.status == Trove.TroveStatus.open)
        .where(~column.in_(subquery))
    )
    remaining_troves_sum = await db.fetch_val(remaining_troves_sum_query)

    results = [
        DecimalLabelledSeries(value=trove["value"], label=trove["label"])
        for trove in top_troves
    ]

    if remaining_troves_sum:
        results.append(
            DecimalLabelledSeries(value=remaining_troves_sum, label="Others")
        )

    return LargePositionsResponse(positions=results)


@cached(ttl=300, cache=Cache.MEMORY)
async def get_vault_recent_events(manager_id: int, period: Period):
    start_timestamp = apply_period(period)
    liquidations_7d = await db.fetch_val(
        query=(
            select([func.count(distinct(TroveSnapshot.liquidation_id))])
            .join(Trove, Trove.id == TroveSnapshot.trove_id)
            .where(
                and_(
                    Trove.manager_id == manager_id,
                    TroveSnapshot.block_timestamp >= start_timestamp,
                )
            )
        )
    )

    redemptions_7d = await db.fetch_val(
        query=(
            select([func.count(distinct(TroveSnapshot.redemption_id))])
            .join(Trove, Trove.id == TroveSnapshot.trove_id)
            .where(
                and_(
                    Trove.manager_id == manager_id,
                    TroveSnapshot.block_timestamp >= start_timestamp,
                )
            )
        )
    )

    trove_overview = SingleVaultEvents(
        liquidations=liquidations_7d,
        redemptions=redemptions_7d,
    )

    return trove_overview


@cached(ttl=300, cache=Cache.MEMORY)
async def get_vault_cr(
    manager_id: int, period: Period
) -> SingleVaultCollateralRatioResponse:
    start_timestamp = apply_period(period)
    query = (
        select(
            [
                TroveManagerSnapshot.collateral_ratio.label("value"),
                TroveManagerSnapshot.block_timestamp.label("timestamp"),
            ]
        )
        .where(
            and_(
                TroveManagerSnapshot.manager_id == manager_id,
                TroveManagerSnapshot.block_timestamp >= start_timestamp,
            )
        )
        .order_by(TroveManagerSnapshot.block_timestamp)
    )

    results = await db.fetch_all(query)
    ratio = [DecimalTimeSeries(**r) for r in results]
    return SingleVaultCollateralRatioResponse(ratio=ratio)


@cached(ttl=300, cache=Cache.MEMORY)
async def get_vault_count(
    manager_id: int, period: Period
) -> SingleVaultTroveCountResponse:
    start_timestamp = apply_period(period)
    query = (
        select(
            [
                TroveManagerSnapshot.open_troves.label("value"),
                TroveManagerSnapshot.block_timestamp.label("timestamp"),
            ]
        )
        .where(
            and_(
                TroveManagerSnapshot.manager_id == manager_id,
                TroveManagerSnapshot.block_timestamp >= start_timestamp,
            )
        )
        .order_by(TroveManagerSnapshot.block_timestamp)
    )

    results = await db.fetch_all(query)
    counts = [DecimalTimeSeries(**r) for r in results]
    return SingleVaultTroveCountResponse(count=counts)
