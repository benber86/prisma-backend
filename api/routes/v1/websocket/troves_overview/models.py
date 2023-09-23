from pydantic import BaseModel

from api.routes.v1.websocket.models import Payload


class TroveManagerDetails(BaseModel):
    name: str
    address: str
    tvl: float
    debt: float
    debt_cap: float
    cr: float
    mcr: float
    rate: float
    price: float
    open_troves: int
    closed_troves: int
    liq_troves: int
    red_troves: int


class TroveOverviewSettings(BaseModel):
    chain: str


class TroveOverviewPayload(BaseModel):
    channel: str
    subscription: TroveOverviewSettings
    type: Payload
    payload: list[TroveManagerDetails]
