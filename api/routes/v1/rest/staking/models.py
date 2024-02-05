from pydantic import BaseModel

from api.models.common import (
    DecimalLabelledSeries,
    DecimalTimeSeries,
    GroupBy,
    Period,
)


class FilterSet(BaseModel):
    period: Period = Period.month
    groupby: GroupBy = GroupBy.week

    class Config:
        use_enum_values = True


class PeriodFilterSet(BaseModel):
    period: Period = Period.month

    class Config:
        use_enum_values = True


class AggregateOperation(BaseModel):
    amount: float
    amount_usd: float
    count: int
    timestamp: int


class SingleOperation(BaseModel):
    amount: float
    amount_usd: float
    timestamp: int


class AggregateStakingFlowResponse(BaseModel):
    withdrawals: list[AggregateOperation]
    deposits: list[AggregateOperation]


class StakingTvlResponse(BaseModel):
    tvl: list[DecimalTimeSeries]


class StakingTotalSupplyResponse(BaseModel):
    supply: list[DecimalTimeSeries]


class StakingSnapshotModel(BaseModel):
    token_balance: float
    token_supply: float
    tvl: float
    total_apr: float
    apr_breakdown: list[dict]
    timestamp: int


class StakingSnapshotsResponse(BaseModel):
    Snapshots: list[StakingSnapshotModel]


class RewardsClaimed(BaseModel):
    token_address: str
    token_symbol: str
    amount: float
    amount_usd: float
    timestamp: int
    transaction_hash: str


class UserDetails(BaseModel):
    claims: list[RewardsClaimed]
    withdrawals: list[SingleOperation]
    deposits: list[SingleOperation]
    stake_size: list[SingleOperation]


class DistributionResponse(BaseModel):
    distribution: list[DecimalLabelledSeries]
