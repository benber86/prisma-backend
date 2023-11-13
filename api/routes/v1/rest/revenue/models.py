from pydantic import BaseModel

from api.models.common import Period


class PeriodFilterSet(BaseModel):
    period: Period = Period.month

    class Config:
        use_enum_values = True


class RevenueSnapshotModel(BaseModel):
    unlock_penalty_revenue_usd: float
    borrowing_fees_revenue_usd: float
    redemption_fees_revenue_usd: float
    timestamp: int


class RevenueSnapshotsResponse(BaseModel):
    snapshots: list[RevenueSnapshotModel]


class RevenueBreakdownResponse(BaseModel):
    unlock_penalty: float
    borrowing_fees: float
    redemption_fees: float
