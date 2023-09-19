import logging
from typing import Type

from fastapi import WebSocket
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, set[str]] = {}
        self.subscription_settings: dict[str, Type[BaseModel]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = set()

    async def disconnect(self, websocket: WebSocket):
        del self.active_connections[websocket]
        await websocket.close()

    async def broadcast(self, message: str, channel: str):
        for connection, subscriptions in self.active_connections.items():
            if channel in subscriptions:
                await connection.send_text(message)

    @staticmethod
    async def send_message(websocket: WebSocket, message: str):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            pass

    def subscribe(
        self, websocket: WebSocket, channel: str, subscription: Type[BaseModel]
    ):
        if channel not in self.subscription_settings:
            self.subscription_settings[channel] = subscription
        if websocket in self.active_connections:
            self.active_connections[websocket].add(channel)

    def unsubscribe(self, websocket: WebSocket, channel: str):
        if (
            websocket in self.active_connections
            and channel in self.active_connections[websocket]
        ):
            self.active_connections[websocket].remove(channel)


manager = ConnectionManager()
