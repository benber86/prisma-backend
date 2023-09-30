from pydantic import BaseModel

from api.models.common import (
    DecimalLabelledSeries,
    DecimalTimeSeries,
    IntegerLabelledSeries,
)


class PriceResponse(BaseModel):
    prices: list[DecimalTimeSeries]


class PriceHistogramResponse(BaseModel):
    histogram: list[IntegerLabelledSeries]


class HoldersResponse(BaseModel):
    holders: list[DecimalLabelledSeries]
