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
