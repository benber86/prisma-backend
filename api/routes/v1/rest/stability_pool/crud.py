import pandas as pd
from aiocache import Cache, cached
from sqlalchemy import and_, case, desc, func, or_, select
from web3 import Web3

from api.models.common import DecimalTimeSeries, Period
from api.routes.utils.histogram import make_histogram
from api.routes.utils.time import SECONDS_IN_DAY, apply_period
from api.routes.v1.rest.stability_pool.models import (
    DistributionResponse,
    PoolDepositsWithdrawalsHistorical,
    PoolStableOperation,
)
from database.engine import db
from database.models.common import User
from database.models.troves import (
    StabilityPool,
    StabilityPoolOperation,
    StabilityPoolSnapshot,
)


@cached(ttl=300, cache=Cache.MEMORY)
async def get_pool_amounts(
    chain_id: int, period: Period, withdraw: bool
) -> list[DecimalTimeSeries]:
    if withdraw:
        value_column = StabilityPoolSnapshot.total_collateral_withdrawn_usd
    else:
        value_column = StabilityPoolSnapshot.total_deposited

    start_timestamp = apply_period(period)
    query = (
        select([value_column, StabilityPoolSnapshot.block_timestamp])
        .join(StabilityPool, StabilityPool.id == StabilityPoolSnapshot.pool_id)
        .where(
            and_(
                StabilityPool.chain_id == chain_id,
                StabilityPoolSnapshot.block_timestamp >= start_timestamp,
            )
        )
        .order_by(StabilityPoolSnapshot.block_timestamp)
    )

    results = await db.fetch_all(query)
    return [
        DecimalTimeSeries(
            value=result[value_column.name],
            timestamp=result["block_timestamp"],
        )
        for result in results
    ]


@cached(ttl=300, cache=Cache.MEMORY)
async def get_main_stable_deposits_withdrawals(
    chain_id: int, period: Period, withdrawal: bool
) -> list[PoolStableOperation]:
    start_timestamp = apply_period(period)
    if withdrawal:
        operation_type = (
            StabilityPoolOperation.StabilityPoolOperationType.stable_withdrawal
        )
    else:
        operation_type = (
            StabilityPoolOperation.StabilityPoolOperationType.stable_deposit
        )

    query = (
        select(
            [
                StabilityPoolOperation.stable_amount,
                StabilityPoolOperation.block_timestamp,
                User.id.label("user_address"),
            ]
        )
        .join(User, User.id == StabilityPoolOperation.user_id)
        .where(
            and_(
                StabilityPoolOperation.operation == operation_type,
                StabilityPool.chain_id == chain_id,
                StabilityPoolOperation.block_timestamp >= start_timestamp,
            )
        )
        .order_by(desc(StabilityPoolOperation.stable_amount))
        .limit(10)
    )

    results = await db.fetch_all(query)

    return [
        PoolStableOperation(
            amount=result["stable_amount"],
            timestamp=result["block_timestamp"],
            user=Web3.to_checksum_address(result["user_address"]),
        )
        for result in results
    ]


@cached(ttl=300, cache=Cache.MEMORY)
async def get_stable_deposits_and_withdrawals(
    chain_id: int, period: Period
) -> PoolDepositsWithdrawalsHistorical:
    start_timestamp = apply_period(period)
    query = (
        select(
            [
                (
                    func.floor(
                        StabilityPoolOperation.block_timestamp / SECONDS_IN_DAY
                    )
                    * SECONDS_IN_DAY
                ).label("day"),
                func.sum(
                    case(
                        [
                            (
                                StabilityPoolOperation.operation
                                == StabilityPoolOperation.StabilityPoolOperationType.stable_deposit,
                                StabilityPoolOperation.stable_amount,
                            ),
                        ],
                        else_=-StabilityPoolOperation.stable_amount,
                    )
                ).label("total_amount"),
                StabilityPoolOperation.operation,
            ]
        )
        .join(
            StabilityPool, StabilityPool.id == StabilityPoolOperation.pool_id
        )
        .where(
            and_(
                StabilityPool.chain_id == chain_id,
                StabilityPoolOperation.block_timestamp >= start_timestamp,
                or_(
                    StabilityPoolOperation.operation
                    == StabilityPoolOperation.StabilityPoolOperationType.stable_deposit,
                    StabilityPoolOperation.operation
                    == StabilityPoolOperation.StabilityPoolOperationType.stable_withdrawal,
                ),
            )
        )
        .group_by("day", StabilityPoolOperation.operation)
        .order_by("day")
    )

    results = await db.fetch_all(query)

    deposits = []
    withdrawals = []
    for result in results:
        time_series = DecimalTimeSeries(
            value=float(result["total_amount"]), timestamp=int(result["day"])
        )
        if (
            result["operation"]
            == StabilityPoolOperation.StabilityPoolOperationType.stable_deposit
        ):
            deposits.append(time_series)
        else:
            withdrawals.append(time_series)

    return PoolDepositsWithdrawalsHistorical(
        deposits=deposits, withdrawals=withdrawals
    )


async def get_deposit_histogram(chain_id: int) -> DistributionResponse:
    subquery = (
        select(
            [
                StabilityPoolOperation.user_id,
                func.max(StabilityPoolOperation.index).label("max_index"),
            ]
        )
        .join(
            StabilityPool, StabilityPool.id == StabilityPoolOperation.pool_id
        )
        .where(
            and_(
                StabilityPool.chain_id == chain_id,
                StabilityPoolOperation.operation
                == StabilityPoolOperation.StabilityPoolOperationType.stable_deposit,
            )
        )
        .group_by(StabilityPoolOperation.user_id)
    ).alias("subquery")

    query = select([StabilityPoolOperation.user_deposit]).join(
        subquery,
        and_(
            StabilityPoolOperation.user_id == subquery.c.user_id,
            StabilityPoolOperation.index == subquery.c.max_index,
        ),
    )

    results = await db.fetch_all(query)
    series = pd.Series([float(r["user_deposit"]) for r in results])
    distrib = make_histogram(series)
    return DistributionResponse(distribution=distrib)
