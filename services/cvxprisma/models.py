from pydantic import BaseModel


class StakingData(BaseModel):
    id: str
    withdraw_count: int
    deposit_count: int
    payout_count: int
    snapshot_count: int
