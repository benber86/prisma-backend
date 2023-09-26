from pydantic import BaseModel

from api.models.common import DecimalLabelledSeries, DecimalTimeSeries


class PoolDepositResponse(BaseModel):
    deposits: list[DecimalTimeSeries]


class PoolCumulativeWithdrawalResponse(BaseModel):
    withdrawals: list[DecimalTimeSeries]


class PoolStableOperation(BaseModel):
    user: str
    amount: float
    timestamp: int
    hash: str


class PoolStableTopResponse(BaseModel):
    operations: list[PoolStableOperation]


class PoolDepositsWithdrawalsHistorical(BaseModel):
    withdrawals: list[DecimalTimeSeries]
    deposits: list[DecimalTimeSeries]


class DistributionResponse(BaseModel):
    distribution: list[DecimalLabelledSeries]
