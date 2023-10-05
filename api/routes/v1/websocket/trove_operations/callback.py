import logging

from api.routes.v1.websocket.manager import manager
from api.routes.v1.websocket.trove_operations.models import (
    TroveOperationsPayload,
)

logger = logging.getLogger()


async def trove_operations_callback(data: TroveOperationsPayload):
    channel_sub = (
        f"{data.channel}_{data.subscription.chain}_{data.subscription.manager}"
    )
    await manager.broadcast(data.json(), channel_sub)
