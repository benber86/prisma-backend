from enum import Enum

from pydantic import BaseModel

from api.models.common import GroupBy, Period


class FilterSet(BaseModel):
    period: Period = Period.month
    groupby: GroupBy = GroupBy.week

    class Config:
        use_enum_values = True


class OwnershipProposalDetail(BaseModel):
    creator: str
    creator_label: str | None
    status: str
    index: int
    data: list[dict]
    decode_data: str
    required_weight: int
    received_weight: int
    can_execute_after: int
    vote_count: int
    execution_tx: str
    block_number: int
    block_timestamp: int
    transaction_hash: str


class OwnershipProposalDetailResponse(BaseModel):
    proposals: list[OwnershipProposalDetail]


class OrderBy(Enum):
    creator = "creator"
    received_weight = "received_weight"
    required_weight = "required_weight"
    vote_count = "vote_count"
    block_timestamp = "block_timestamp"


class OrderFilter(BaseModel):
    order_by: OrderBy = OrderBy.block_timestamp
    desc: bool = True
    creator_filter: str | None
    decode_data_filter: str | None

    class Config:
        use_enum_values = True
