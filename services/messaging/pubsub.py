import asyncio
import logging

import aioredis

from services.messaging.handler import (
    REDIS_MESSAGING_CHANNELS,
    parse_incoming_messages,
)
from services.messaging.redis import get_redis_client

logger = logging.getLogger()


async def publish_message(
    channel: str, data: str, retries: int = 3, delay: int = 5
):
    for _ in range(retries):
        try:
            redis_client = await get_redis_client("celery")
            await redis_client.publish(channel, data)
            return
        except aioredis.ConnectionError:
            await asyncio.sleep(delay)
    raise Exception("Failed to publish after multiple retries.")


async def listen_for_redis_notifications():
    while True:
        try:
            redis_client = await get_redis_client("fastapi")

            pubsub = redis_client.pubsub()
            for channel in REDIS_MESSAGING_CHANNELS:
                logger.info(f"Subscribing to: {channel}")
                await pubsub.subscribe(channel)

            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True
                )
                if message and message["type"] == "message":

                    message_content = (
                        message["data"].decode("utf-8")
                        if isinstance(message["data"], bytes)
                        else message["data"]
                    )
                    channel_name = (
                        message["channel"].decode("utf-8")
                        if isinstance(message["channel"], bytes)
                        else message["channel"]
                    )

                    await parse_incoming_messages(
                        channel=channel_name, data=message_content
                    )
        except aioredis.ConnectionError as e:
            logger.error(f"Connection error for redis messaging {e}")
            await asyncio.sleep(5)
