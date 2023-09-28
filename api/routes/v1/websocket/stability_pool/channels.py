import logging

from fastapi import WebSocket

from api.routes.v1.websocket.manager import manager
from api.routes.v1.websocket.models import Action, Channels, Payload
from api.routes.v1.websocket.stability_pool.crud import get_pool_operations
from api.routes.v1.websocket.stability_pool.models import (
    StabilityPoolPayload,
    StabilityPoolSettings,
)
from utils.const import CHAINS

logger = logging.getLogger()


async def parse_stability_pool_client_message(
    websocket: WebSocket,
    action: Action,
    channel_settings: list[StabilityPoolSettings],
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
            manager.subscribe(websocket, channel_sub, settings)
        elif action == Action.snapshots:
            page = settings.pagination.page if settings.pagination else 1
            items = (
                min(settings.pagination.items, 100)
                if settings.pagination
                else 10
            )
            operations = await get_pool_operations(chain_id, page, items)
            data = StabilityPoolPayload(
                channel=channel,
                subscription=settings,
                type=Payload.snapshot,
                payload=operations,
            )
            await manager.send_message(websocket, data.json())

        elif action == Action.unsubscribe:
            await manager.unsubscribe(websocket, channel_sub)
