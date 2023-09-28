from enum import Enum

from pydantic import BaseModel

from api.models.common import Pagination
from api.routes.v1.websocket.models import Payload


class StabilityPoolOperationType(Enum):
    STABLE_DEPOSIT = "stableDeposit"
    STABLE_WITHDRAWAL = "stableWithdrawal"
    COLLATERAL_WITHDRAWAL = "collateralWithdrawal"


class StabilityPoolOperationDetails(BaseModel):
    user: str
    operation: StabilityPoolOperationType
    amount: float
    hash: str


class StabilityPoolSettings(BaseModel):
    chain: str
    pagination: Pagination | None


class StabilityPoolPayload(BaseModel):
    channel: str
    subscription: StabilityPoolSettings
    type: Payload
    payload: list[StabilityPoolOperationDetails]
