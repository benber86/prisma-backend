import logging

from fastapi import WebSocket

from api.routes.v1.websocket.manager import manager
from api.routes.v1.websocket.models import Action, Channels, Payload
from api.routes.v1.websocket.trove_operations.crud import get_trove_operations
from api.routes.v1.websocket.trove_operations.models import (
    TroveOperationsPayload,
    TroveOperationsSettings,
)
from database.queries.trove_manager import get_manager_id_by_address_and_chain
from utils.const import CHAINS

logger = logging.getLogger()


async def parse_trove_operation_client_message(
    websocket: WebSocket,
    action: Action,
    channel_settings: list[TroveOperationsSettings],
):
    for settings in channel_settings:
        if settings.chain not in CHAINS:
            await manager.send_message(
                websocket, f"Chain {settings.chain} not found"
            )
            continue
        chain_id = CHAINS[settings.chain]
        trove_manager = settings.manager.lower()
        manager_id = await get_manager_id_by_address_and_chain(
            chain_id=chain_id, address=trove_manager
        )
        if not manager_id:
            await manager.send_message(
                websocket, f"Manager {settings.manager} not found"
            )
            continue

        channel = Channels.trove_operations.value
        channel_sub = f"{channel}_{settings.chain}_{trove_manager}"
        if action == Action.subscribe:
            manager.subscribe(websocket, channel_sub, settings)
        elif action == Action.snapshots:
            page = settings.pagination.page if settings.pagination else 1
            items = (
                min(settings.pagination.items, 100)
                if settings.pagination
                else 10
            )
            operations = await get_trove_operations(manager_id, page, items)
            data = TroveOperationsPayload(
                channel=channel,
                subscription=settings,
                type=Payload.snapshot,
                payload=operations,
            )
            await manager.send_message(websocket, data.json())

        elif action == Action.unsubscribe:
            await manager.unsubscribe(websocket, channel_sub)
