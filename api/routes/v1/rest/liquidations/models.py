from enum import Enum

from pydantic import BaseModel

from api.models.common import GroupBy, PaginationReponse, Period


class FilterSet(BaseModel):
    period: Period = Period.month
    groupby: GroupBy = GroupBy.week

    class Config:
        use_enum_values = True


class AggregateLiquidation(BaseModel):
    liquidated: float
    count: int
    timestamp: int


class AggregateLiquidationResponse(BaseModel):
    liquidations: list[AggregateLiquidation]


class LiquidationDescription(BaseModel):
    liquidator: str
    liquidated_debt: float
    liquidated_collateral: float
    liquidated_collateral_usd: float
    collateral_gas_compensation: float
    collateral_gas_compensation_usd: float
    debt_gas_compensation: float
    troves_affected: list[str]
    troves_affected_count: int
    transaction: str
    timestamp: int


class ListLiquidationResponse(BaseModel):
    pagination: PaginationReponse
    liquidations: list[LiquidationDescription]


class OrderBy(Enum):
    liquidator = "liquidator"
    liquidated_debt = "liquidated_debt"
    liquidated_collateral = "liquidated_collateral"
    troves_affected_count = "troves_affected_count"
    block_timestamp = "block_timestamp"


class OrderFilter(BaseModel):
    order_by: OrderBy = OrderBy.block_timestamp
    desc: bool = True
    liquidator_filter: str | None
    trove_filter: str | None

    class Config:
        use_enum_values = True
