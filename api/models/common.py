from enum import Enum

from pydantic import BaseModel


class Period(Enum):
    week = "7d"
    month = "1m"
    trimester = "3m"
    semester = "6m"
    all = "all"


class GroupBy(Enum):
    week = "week"
    month = "month"
    day = "day"
    year = "year"


class Denomination(Enum):
    debt = "debt"
    collateral = "collateral"


class Pagination(BaseModel):
    items: int = 10
    page: int = 1


class PaginationReponse(BaseModel):
    total_records: int
    total_pages: int
    items: int
    page: int


class DecimalTimeSeries(BaseModel):
    value: float
    timestamp: int


class DecimalLabelledSeries(BaseModel):
    value: float
    label: str


class IntegerLabelledSeries(BaseModel):
    value: int
    label: str
