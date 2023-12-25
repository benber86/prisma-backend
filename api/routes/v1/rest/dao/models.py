from enum import Enum

from pydantic import BaseModel

from api.models.common import DecimalTimeSeries, GroupBy, Period


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
    count: int


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


class WeeklyUserVote(BaseModel):
    receiver_id: int
    receiver_address: str
    receiver_label: str
    points: int


class WeeklyUserVoteData(BaseModel):
    week: int
    votes: list[WeeklyUserVote]


class WeeklyUserVoteDataResponse(BaseModel):
    votes: list[WeeklyUserVoteData]


class UserVote(BaseModel):
    week: int
    receiver_id: int | None
    receiver_address: str | None
    receiver_label: str | None
    points: int | None
    clearance: bool
    block_number: int
    block_timestamp: int
    transaction_hash: str


class UserVoteResponse(BaseModel):
    votes: list[UserVote]


class UserOwnershipVote(BaseModel):
    week: int
    proposal_index: int
    account_weight: int
    decisive: bool
    block_number: int
    block_timestamp: int
    transaction_hash: str


class UserOwnershipVoteResponse(BaseModel):
    votes: list[UserOwnershipVote]


class WeeklyClaimData(BaseModel):
    week: int
    eligible: float
    self_claimed: float
    delegate_claimed: float
    left_over: float


class WeeklyClaimDataResponse(BaseModel):
    claims: list[WeeklyClaimData]


class WeeklyBoostUsage(BaseModel):
    boost: list[DecimalTimeSeries]


class HistoricalBoostFees(BaseModel):
    boost: list[DecimalTimeSeries]
