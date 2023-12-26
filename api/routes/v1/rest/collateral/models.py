from enum import Enum

from pydantic import BaseModel

from api.models.common import DecimalTimeSeries


class CollateralPrices(BaseModel):
    market: list[DecimalTimeSeries]
    oracle: list[DecimalTimeSeries]


class CollateralPriceImpact(BaseModel):
    amount: float
    impact: float


class CollateralPriceImpactResponse(BaseModel):
    impact: list[CollateralPriceImpact]


class CollateralGeneralInfo(BaseModel):
    price: float
    supply: float
    tvl: float
    share: float
    risk: str


class CollateralGeneralInfoReponse(BaseModel):
    info: CollateralGeneralInfo


class StakeZapInfo(BaseModel):
    amount: float
    block_timestamp: int
    block_number: int
    tx_hash: str


class StakeZapResponse(BaseModel):
    zaps: list[StakeZapInfo]
    count: int
    total_amount: float


class OrderBy(Enum):
    creator = "amount"
    block_timestamp = "block_timestamp"


class OrderFilter(BaseModel):
    order_by: OrderBy = OrderBy.block_timestamp
    desc: bool = True

    class Config:
        use_enum_values = True
