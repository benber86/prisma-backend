from pydantic import BaseModel

from api.models.common import DecimalTimeSeries, IntegerLabelledSeries


class PriceResponse(BaseModel):
    prices: list[DecimalTimeSeries]


class PriceHistogramResponse(BaseModel):
    histogram: list[IntegerLabelledSeries]
