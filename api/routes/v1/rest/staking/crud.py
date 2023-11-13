import json

import numpy as np
import pandas as pd
from aiocache import Cache, cached
from sqlalchemy import and_, case, func, join, select

from api.models.common import DecimalTimeSeries
from api.routes.utils.histogram import make_histogram
from api.routes.utils.time import apply_period
from api.routes.v1.rest.staking.models import (
    AggregateOperation,
    AggregateStakingFlowResponse,
    DistributionResponse,
    FilterSet,
    PeriodFilterSet,
    RewardsClaimed,
    SingleOperation,
    StakingSnapshotModel,
    StakingSnapshotsResponse,
    StakingTvlResponse,
    UserDetails,
)
from database.engine import db
from database.models.cvxprisma import (
    RewardPaid,
    StakeEvent,
    StakingBalance,
    StakingSnapshot,
)
from utils.const import CVXPRISMA_STAKING


@cached(ttl=60, cache=Cache.MEMORY)
async def get_aggregated_flow(
    filter_set: FilterSet, staking_contract: str = CVXPRISMA_STAKING
) -> AggregateStakingFlowResponse:
    start_timestamp = apply_period(filter_set.period)

    rounded_timestamp = func.date_trunc(
        filter_set.groupby, func.to_timestamp(StakeEvent.block_timestamp)
    )

    query = (
        select(
            StakeEvent.operation,
            func.sum(StakeEvent.amount).label("amount"),
            func.sum(StakeEvent.amount_usd).label("amount_usd"),
            func.count().label("count"),
            func.extract("epoch", rounded_timestamp).label("timestamp"),
        )
        .where(
            and_(
                StakeEvent.block_timestamp >= start_timestamp,
                StakeEvent.staking_id.ilike(
                    staking_contract
                ),  # Filter by staking_contract
            )
        )
        .group_by(StakeEvent.operation, rounded_timestamp)
        .order_by(rounded_timestamp)
    )

    results = await db.fetch_all(query)

    withdrawals = []
    deposits = []
    for result in results:
        operation = AggregateOperation(
            amount=float(result["amount"]),
            amount_usd=float(result["amount_usd"]),
            count=result["count"],
            timestamp=int(result["timestamp"]),
        )
        if result["operation"] == StakeEvent.StakeOperation.withdraw:
            withdrawals.append(operation)
        else:
            deposits.append(operation)

    return AggregateStakingFlowResponse(
        withdrawals=withdrawals, deposits=deposits
    )


@cached(ttl=60, cache=Cache.MEMORY)
async def get_aggregated_tvl(
    filter_set: FilterSet, staking_contract: str = CVXPRISMA_STAKING
) -> StakingTvlResponse:
    start_timestamp = apply_period(filter_set.period)

    rounded_timestamp = func.date_trunc(
        filter_set.groupby, func.to_timestamp(StakingSnapshot.timestamp)
    )

    query = (
        select(
            [
                func.avg(StakingSnapshot.tvl).label("total_tvl"),
                func.extract("epoch", rounded_timestamp).label("timestamp"),
            ]
        )
        .where(
            and_(
                StakingSnapshot.timestamp >= start_timestamp,
                StakingSnapshot.staking_id.ilike(
                    staking_contract
                ),  # Filter by staking_contract
            )
        )
        .group_by(rounded_timestamp)
        .order_by(rounded_timestamp)
    )

    results = await db.fetch_all(query)

    tvl_timeseries = [
        DecimalTimeSeries(
            value=result["total_tvl"], timestamp=int(result["timestamp"])
        )
        for result in results
    ]

    return StakingTvlResponse(tvl=tvl_timeseries)


@cached(ttl=60, cache=Cache.MEMORY)
async def get_snapshots(
    filter_set: PeriodFilterSet, staking_contract: str = CVXPRISMA_STAKING
) -> StakingSnapshotsResponse:
    start_timestamp = apply_period(filter_set.period)
    query = (
        select(StakingSnapshot)
        .where(
            and_(
                StakingSnapshot.timestamp >= start_timestamp,
                StakingSnapshot.staking_id.ilike(
                    staking_contract
                ),  # Filter by staking_contract
            )
        )
        .order_by(StakingSnapshot.timestamp)
    )

    results = await db.fetch_all(query)

    snapshots = [
        StakingSnapshotModel(
            token_balance=result.token_balance,
            token_supply=result.token_supply,
            tvl=result.tvl,
            total_apr=result.total_apr,
            apr_breakdown=json.loads(result.apr_breakdown),
            timestamp=result.timestamp,
        )
        for result in results
    ]

    return StakingSnapshotsResponse(Snapshots=snapshots)


async def _get_stake_size(
    user_id: str, staking_contract: str
) -> list[SingleOperation]:
    # Find the earliest record of the user's stake to limit the price data query
    earliest_stake_record = await db.fetch_one(
        select([func.min(StakingBalance.timestamp)]).where(
            and_(
                StakingBalance.user_id.ilike(user_id),
                StakingBalance.staking_id.ilike(staking_contract),
            )
        )
    )
    earliest_date = earliest_stake_record[0]
    if not earliest_date:
        return []

    # Retrieve user's staking balances
    user_balances = await db.fetch_all(
        select([StakingBalance.stake_size, StakingBalance.timestamp])
        .where(
            and_(
                StakingBalance.user_id.ilike(user_id),
                StakingBalance.staking_id.ilike(staking_contract),
            )
        )
        .order_by(StakingBalance.timestamp)
    )

    # Subquery that selects the latest timestamp for each day
    latest_snapshot_subquery = (
        select(
            [
                func.date_trunc(
                    "day", func.to_timestamp(StakingSnapshot.timestamp)
                ).label("truncated_date"),
                func.max(StakingSnapshot.timestamp).label("latest_timestamp"),
            ]
        )
        .where(
            and_(
                StakingSnapshot.timestamp >= earliest_date,
                StakingSnapshot.staking_id.ilike(
                    staking_contract
                ),  # Filter by staking_contract
            )
        )
        .group_by("truncated_date")
        .subquery()
    )

    price_snapshots_query = (
        select(
            [
                latest_snapshot_subquery.c.truncated_date,
                (StakingSnapshot.tvl / StakingSnapshot.token_balance).label(
                    "token_price"
                ),
            ]
        )
        .select_from(
            join(
                StakingSnapshot,
                latest_snapshot_subquery,
                and_(
                    StakingSnapshot.timestamp
                    == latest_snapshot_subquery.c.latest_timestamp,
                    StakingSnapshot.token_balance
                    != 0,  # Avoid division by zero
                ),
            )
        )
        .order_by(latest_snapshot_subquery.c.truncated_date)
    )

    price_snapshots = await db.fetch_all(price_snapshots_query)

    balances_df = pd.DataFrame([dict(row) for row in user_balances])
    prices_df = pd.DataFrame([dict(row) for row in price_snapshots])
    balances_df["timestamp"] = balances_df["timestamp"].astype(np.int64)
    prices_df["truncated_date"] = (
        pd.to_datetime(prices_df["truncated_date"]).astype(np.int64) // 10**9
    )

    balances_df.sort_values(by="timestamp", inplace=True)
    prices_df.sort_values(by="truncated_date", inplace=True)

    merged_df = pd.merge_asof(
        balances_df,
        prices_df,
        left_on="timestamp",
        right_on="truncated_date",
        direction="backward",
    )

    combined_df = pd.concat([merged_df, prices_df], axis=0).sort_values(
        by="timestamp"
    )
    combined_df["stake_size"] = combined_df["stake_size"].ffill()
    combined_df["timestamp"] = combined_df["timestamp"].fillna(
        combined_df["truncated_date"]
    )

    combined_df = combined_df[~combined_df["token_price"].isna()]

    stake_size_data = combined_df.to_dict(orient="records")

    return [
        SingleOperation(
            amount=row["stake_size"],
            amount_usd=row["token_price"] * row["stake_size"],
            timestamp=row["timestamp"],
        )
        for row in stake_size_data
    ]


@cached(ttl=60, cache=Cache.MEMORY)
async def get_user_details(
    user_id: str, staking_contract: str = CVXPRISMA_STAKING
) -> UserDetails:
    # Fetch claims
    rewards_query = (
        select(RewardPaid)
        .where(
            and_(
                RewardPaid.user_id.ilike(user_id),
                RewardPaid.staking_id.ilike(staking_contract),
            )
        )
        .order_by(RewardPaid.block_timestamp)
    )
    rewards_results = await db.fetch_all(rewards_query)
    claims = [
        RewardsClaimed(
            token_address=reward.token_address,
            token_symbol=reward.token_symbol,
            amount=float(reward.amount),
            amount_usd=float(reward.amount_usd),
            timestamp=reward.block_timestamp,
            transaction_hash=reward.transaction_hash,
        )
        for reward in rewards_results
    ]

    # Fetch withdrawals and deposits
    stake_events_query = (
        select(StakeEvent)
        .where(
            and_(
                StakeEvent.user_id.ilike(user_id),
                StakeEvent.staking_id.ilike(staking_contract),
            )
        )
        .order_by(StakeEvent.block_timestamp)
    )
    stake_events_results = await db.fetch_all(stake_events_query)

    withdrawals = []
    deposits = []

    for event in stake_events_results:
        operation = SingleOperation(
            amount=float(event.amount),
            amount_usd=float(event.amount_usd),
            timestamp=event.block_timestamp,
        )
        if event.operation == StakeEvent.StakeOperation.withdraw.value:
            withdrawals.append(operation)
        else:
            deposits.append(operation)

    # Construct UserDetails
    user_details = UserDetails(
        claims=claims,
        withdrawals=withdrawals,
        deposits=deposits,
        stake_size=await _get_stake_size(user_id, staking_contract),
    )

    return user_details


@cached(ttl=60, cache=Cache.MEMORY)
async def get_staking_balance_histogram(
    staking_contract: str = CVXPRISMA_STAKING,
) -> DistributionResponse:
    most_recent_snapshot = await db.fetch_one(
        select([StakingSnapshot.tvl, StakingSnapshot.token_balance])
        .where(StakingSnapshot.staking_id.ilike(staking_contract))
        .order_by(StakingSnapshot.timestamp.desc())
        .limit(1)
    )

    latest_price = (
        most_recent_snapshot["tvl"] / most_recent_snapshot["token_balance"]
        if (
            most_recent_snapshot and most_recent_snapshot["token_balance"] != 0
        )
        else 0
    )

    subquery = (
        select(
            [
                StakingBalance.user_id,
                func.max(StakingBalance.timestamp).label("max_timestamp"),
            ]
        )
        .where(StakingBalance.staking_id.ilike(staking_contract))
        .group_by(StakingBalance.user_id)
        .subquery()
    )

    query = select([StakingBalance.stake_size]).join(
        subquery,
        and_(
            StakingBalance.user_id == subquery.c.user_id,
            StakingBalance.timestamp == subquery.c.max_timestamp,
            StakingBalance.stake_size >= 0.5,
            StakingBalance.staking_id.ilike(staking_contract),
        ),
    )

    results = await db.fetch_all(query)
    usd_values = [float(r["stake_size"] * latest_price) for r in results]
    series = pd.Series(usd_values)
    distrib = make_histogram(series)
    return DistributionResponse(distribution=distrib)
