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
