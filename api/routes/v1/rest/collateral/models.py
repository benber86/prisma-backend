from pydantic import BaseModel

from api.models.common import DecimalTimeSeries


class CollateralPrices(BaseModel):
    market: list[DecimalTimeSeries]
    oracle: list[DecimalTimeSeries]
