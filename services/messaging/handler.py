import json

from api.routes.v1.websocket.handler import Handler
from api.routes.v1.websocket.troves_overview.callback import (
    trove_overview_callback,
)
from api.routes.v1.websocket.troves_overview.models import (
    TroveOverviewSettings,
)

TROVE_OVERVIEW_UPDATE = "trove_overview_update"
REDIS_MESSAGING_CHANNELS = [TROVE_OVERVIEW_UPDATE]

CALLBACK_MAPPING = {
    TROVE_OVERVIEW_UPDATE: Handler(
        trove_overview_callback, TroveOverviewSettings
    )
}


async def parse_incoming_messages(channel: str, data: str):
    json_data = json.loads(data)
    if channel in CALLBACK_MAPPING:
        await CALLBACK_MAPPING[channel].func(
            CALLBACK_MAPPING[channel].model.parse_obj(json_data)
        )
