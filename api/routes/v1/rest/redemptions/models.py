from enum import Enum

from pydantic import BaseModel

from api.models.common import GroupBy, Period


class FilterSet(BaseModel):
    period: Period = Period.month
    groupby: GroupBy = GroupBy.week

    class Config:
        use_enum_values = True


class AggregateRedemption(BaseModel):
    redeemed: float
    count: int
    timestamp: int


class AggregateRedemptionResponse(BaseModel):
    redemptions: list[AggregateRedemption]


class RedemptionDescription(BaseModel):
    redeemer: str
    attempted_debt_amount: float
    actual_debt_amount: float
    collateral_sent: float
    collateral_sent_usd: float
    collateral_sent_to_redeemer: float
    collateral_sent_to_redeemer_usd: float
    collateral_fee: float
    collateral_fee_usd: float
    troves_affected: list[str]
    troves_affected_count: int
    transaction: str
    timestamp: int


class ListRedemptionResponse(BaseModel):
    redemptions: list[RedemptionDescription]


class OrderBy(Enum):
    redeemer = "redeemer"
    collateral_sent = "collateral_sent"
    actual_debt_amount = "actual_debt_amount"
    troves_affected_count = "troves_affected_count"
    block_timestamp = "block_timestamp"


class OrderFilter(BaseModel):
    order_by: OrderBy = OrderBy.block_timestamp
    desc: bool = True
    redeemer_filter: str | None

    class Config:
        use_enum_values = True
