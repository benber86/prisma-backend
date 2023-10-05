from enum import Enum

from pydantic import BaseModel


class Status(Enum):
    open = "Open"
    closed_by_owner = "Closed"
    closed_by_liquidation = "Closed (Liq.)"
    closed_by_redemption = "Closed (Red.)"


class OrderBy(Enum):
    owner = "owner"
    collateral_usd = "collateral_usd"
    debt = "debt"
    collateral_ratio = "collateral_ratio"
    created_at = "created_at"
    last_update = "last_update"


class TroveEntry(BaseModel):
    owner: str
    status: Status
    collateral_usd: float
    debt: float
    collateral_ratio: float
    created_at: int
    last_update: int


class TroveEntryReponse(BaseModel):
    page: int
    total_entries: int
    troves: list[TroveEntry]


class FilterSet(BaseModel):
    order_by: OrderBy = OrderBy.last_update
    desc: bool = True
    owner_filter: str | None

    class Config:
        use_enum_values = True
