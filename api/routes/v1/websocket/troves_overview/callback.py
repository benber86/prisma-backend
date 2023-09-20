import logging

from api.routes.v1.websocket.manager import manager
from api.routes.v1.websocket.models import Channels, Payload
from api.routes.v1.websocket.troves_overview.crud import (
    get_trove_manager_details,
)
from api.routes.v1.websocket.troves_overview.models import (
    TroveOverviewPayload,
    TroveOverviewSettings,
)
from utils.const import CHAINS

logger = logging.getLogger()


async def trove_overview_callback(data: TroveOverviewSettings):
    chain_id = CHAINS[data.chain]
    channel = Channels.troves_overview.value
    channel_sub = f"{channel}_{chain_id}"
    markets = await get_trove_manager_details(chain_id)
    payload = TroveOverviewPayload(
        channel=channel,
        subscription=data,
        type=Payload.update,
        payload=markets,
    )
    await manager.broadcast(payload.json(), channel_sub)
