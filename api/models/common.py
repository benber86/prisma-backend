from enum import Enum

from pydantic import BaseModel


class Period(Enum):
    month = "1m"
    semester = "6m"
    all = "all"


class Pagination(BaseModel):
    pagination: int = 10
    page: int = 1


class DecimalTimeSeries(BaseModel):
    value: float
    timestamp: int
