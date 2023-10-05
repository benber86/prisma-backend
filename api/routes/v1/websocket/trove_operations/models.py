from pydantic import BaseModel

from api.models.common import Pagination
from api.routes.v1.websocket.models import Payload


class TroveOperation(BaseModel):
    owner: str
    operation: str
    collateral_usd: float
    debt: float
    timestamp: int
    hash: str


class TroveOperationsSettings(BaseModel):
    chain: str
    manager: str
    pagination: Pagination | None


class TroveOperationsPayload(BaseModel):
    channel: str
    subscription: TroveOperationsSettings
    type: Payload
    payload: list[TroveOperation]
