from pydantic import BaseModel

from api.models.common import (
    DecimalLabelledSeries,
    DecimalTimeSeries,
    Denomination,
    Period,
)


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


class DistributionResponse(BaseModel):
    distribution: list[DecimalLabelledSeries]


class CollateralVsDebt(BaseModel):
    unit: Denomination = Denomination.collateral

    class Config:
        use_enum_values = True


class LargePositionsResponse(BaseModel):
    positions: list[DecimalLabelledSeries]


class SingleVaultEvents(BaseModel):
    liquidations: int
    redemptions: int


class SingleVaultEventsReponse(BaseModel):
    info: SingleVaultEvents


class SingleVaultCollateralRatioResponse(BaseModel):
    ratio: list[DecimalTimeSeries]


class SingleVaultTroveCountResponse(BaseModel):
    count: list[DecimalTimeSeries]
