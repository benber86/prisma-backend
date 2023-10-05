import logging
from typing import Any, Callable, NamedTuple, Type

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError, root_validator

from api.routes.v1.websocket.manager import manager
from api.routes.v1.websocket.models import Action, Channels
from api.routes.v1.websocket.stability_pool.channels import (
    parse_stability_pool_client_message,
)
from api.routes.v1.websocket.stability_pool.models import StabilityPoolSettings
from api.routes.v1.websocket.trove_operations.channels import (
    parse_trove_operation_client_message,
)
from api.routes.v1.websocket.trove_operations.models import (
    TroveOperationsSettings,
)
from api.routes.v1.websocket.troves_overview.channels import (
    parse_trove_overview_client_message,
)
from api.routes.v1.websocket.troves_overview.models import (
    TroveOverviewSettings,
)

logger = logging.getLogger()
router = APIRouter()

Handler = NamedTuple(
    "Handler", [("func", Callable[..., Any]), ("model", Type[BaseModel])]
)

CHANNEL_MAP: dict[Channels, Handler] = {
    Channels.troves_overview: Handler(
        parse_trove_overview_client_message, TroveOverviewSettings
    ),
    Channels.stability_pool: Handler(
        parse_stability_pool_client_message, StabilityPoolSettings
    ),
    Channels.trove_operations: Handler(
        parse_trove_operation_client_message, TroveOperationsSettings
    ),
}


class WebSocketMessage(BaseModel):
    action: Action
    channel: Channels
    settings: list[BaseModel]

    @root_validator(pre=True)
    def set_settings_type(cls, values):
        channel = Channels(values.get("channel"))
        if channel in CHANNEL_MAP:
            model = CHANNEL_MAP[channel].model
            values["settings"] = [
                model.parse_obj(setting) for setting in values["settings"]
            ]
        else:
            raise ValueError(f"Unknown channel: {channel}")
        return values


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    while True:
        try:
            data = await websocket.receive_text()
            message = WebSocketMessage.parse_raw(data)
            if message.channel in CHANNEL_MAP:
                await CHANNEL_MAP[message.channel].func(
                    websocket, message.action, message.settings
                )

        except WebSocketDisconnect:
            logger.info(f"Websocket {websocket} disconnected")
            await manager.disconnect(websocket)
            break
        except ValidationError as e:
            await manager.send_message(
                websocket, f"Error in message format: {str(e)}"
            )
        except Exception as e:
            logger.error(e)
