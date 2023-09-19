import logging

from fastapi import WebSocket

from api.routes.v1.websocket.manager import manager
from api.routes.v1.websocket.models import Action, Channels, Payload
from api.routes.v1.websocket.troves_overview.crud import (
    get_trove_manager_details,
)
from api.routes.v1.websocket.troves_overview.models import (
    TroveOverviewPayload,
    TroveOverviewSettings,
)
from utils.const import CHAINS

logger = logging.getLogger()


async def parse_trove_overview_client_message(
    websocket: WebSocket,
    action: Action,
    channel_settings: list[TroveOverviewSettings],
):
    for settings in channel_settings:
        if settings.chain not in CHAINS:
            await manager.send_message(
                websocket, f"Chain {settings.chain} not found"
            )
            continue
        chain_id = CHAINS[settings.chain]
        channel = Channels.troves_overview.value
        channel_sub = f"{channel}_{chain_id}"
        if action == Action.subscribe:
            await manager.send_message(
                websocket, f"Subscription currently unsupported"
            )
        elif action == Action.snapshots:
            page = settings.pagination.page if settings.pagination else 1
            items = (
                min(settings.pagination.pagination, 100)
                if settings.pagination
                else 10
            )
            markets = await get_trove_manager_details(chain_id, page, items)
            data = TroveOverviewPayload(
                channel=channel,
                subscription=settings,
                type=Payload.snapshot,
                payload=markets,
            )
            await manager.send_message(websocket, data.json())

        elif action == Action.unsubscribe:
            await manager.unsubscribe(websocket, channel_sub)
