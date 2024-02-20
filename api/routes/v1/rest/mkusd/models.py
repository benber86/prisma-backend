from pydantic import BaseModel

from api.models.common import (
    DecimalLabelledSeries,
    DecimalTimeSeries,
    IntegerLabelledSeries,
)
from services.prices.liquidity_depth import PoolDepth


class PriceResponse(BaseModel):
    prices: list[DecimalTimeSeries]


class PriceHistogramResponse(BaseModel):
    histogram: list[IntegerLabelledSeries]


class HoldersResponse(BaseModel):
    holders: list[DecimalLabelledSeries]


class HistoricalSupply(BaseModel):
    supply: list[DecimalTimeSeries]


class DepthResponse(BaseModel):
    depth: list[PoolDepth]


class StableInfo(BaseModel):
    price: float
    supply: float
    volume: float
    depth: float


class StableInfoReponse(BaseModel):
    info: StableInfo
