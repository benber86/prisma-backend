import json

from api.routes.v1.websocket.handler import Handler
from api.routes.v1.websocket.stability_pool.callback import (
    stability_pool_callback,
)
from api.routes.v1.websocket.stability_pool.models import StabilityPoolPayload
from api.routes.v1.websocket.trove_operations.callback import (
    trove_operations_callback,
)
from api.routes.v1.websocket.trove_operations.models import (
    TroveOperationsPayload,
)
from api.routes.v1.websocket.troves_overview.callback import (
    trove_overview_callback,
)
from api.routes.v1.websocket.troves_overview.models import (
    TroveOverviewSettings,
)

TROVE_OVERVIEW_UPDATE = "trove_overview_update"
STABILITY_POOL_UPDATE = "stability_pool_update"
TROVE_OPERATIONS_UPDATE = "trove_operations_update"
REDIS_MESSAGING_CHANNELS = [
    TROVE_OVERVIEW_UPDATE,
    STABILITY_POOL_UPDATE,
    TROVE_OPERATIONS_UPDATE,
]

CALLBACK_MAPPING = {
    TROVE_OVERVIEW_UPDATE: Handler(
        trove_overview_callback, TroveOverviewSettings
    ),
    STABILITY_POOL_UPDATE: Handler(
        stability_pool_callback, StabilityPoolPayload
    ),
    TROVE_OPERATIONS_UPDATE: Handler(
        trove_operations_callback, TroveOperationsPayload
    ),
}


async def parse_incoming_messages(channel: str, data: str):
    json_data = json.loads(data)
    if channel in CALLBACK_MAPPING:
        await CALLBACK_MAPPING[channel].func(
            CALLBACK_MAPPING[channel].model.parse_obj(json_data)
        )
