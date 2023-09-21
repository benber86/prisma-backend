from pydantic import BaseModel

from api.models.common import DecimalTimeSeries, Period


class HistoricalTroveManagerCR(BaseModel):
    trove: str
    data: list[DecimalTimeSeries]


class HistoricalCollateralRatioResponse(BaseModel):
    troves: list[HistoricalTroveManagerCR]


class FilterSet(BaseModel):
    period: Period = Period.month

    class Config:
        use_enum_values = True


class HistoricalOpenedTroves(BaseModel):
    trove: str
    data: list[DecimalTimeSeries]


class HistoricalOpenedTrovesResponse(BaseModel):
    troves: list[HistoricalOpenedTroves]
