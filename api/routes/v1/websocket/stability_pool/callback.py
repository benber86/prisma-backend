import logging

from api.routes.v1.websocket.manager import manager
from api.routes.v1.websocket.stability_pool.models import StabilityPoolPayload

logger = logging.getLogger()


async def stability_pool_callback(data: StabilityPoolPayload):
    channel_sub = f"{data.channel}_{data.subscription.chain}"
    await manager.broadcast(data.json(), channel_sub)
