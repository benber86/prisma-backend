from enum import Enum

from pydantic import BaseModel


class Period(Enum):
    week = "7d"
    month = "1m"
    trimester = "6m"
    semester = "6m"
    all = "all"


class Denomination(Enum):
    debt = "debt"
    collateral = "collateral"


class Pagination(BaseModel):
    items: int = 10
    page: int = 1


class DecimalTimeSeries(BaseModel):
    value: float
    timestamp: int


class DecimalLabelledSeries(BaseModel):
    value: float
    label: str
