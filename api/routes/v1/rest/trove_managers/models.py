from pydantic import BaseModel

from api.models.common import DecimalTimeSeries, Period


class HistoricalTroveManagerData(BaseModel):
    manager: str
    data: list[DecimalTimeSeries]


class HistoricalTroveOverviewResponse(BaseModel):
    managers: list[HistoricalTroveManagerData]


class FilterSet(BaseModel):
    period: Period = Period.month

    class Config:
        use_enum_values = True


class HistoricalOpenedTroves(BaseModel):
    manager: str
    data: list[DecimalTimeSeries]


class HistoricalOpenedTrovesResponse(BaseModel):
    managers: list[HistoricalOpenedTroves]


class CollateralRatioDecilesData(BaseModel):
    label: str
    data: float


class CollateralRatioDistributionResponse(BaseModel):
    deciles: list[CollateralRatioDecilesData]
