import aioredis

from settings.config import settings

REDIS_MESSAGING_URL = f"redis://:{settings.REDIS_PASSWORD}@redis:6379/1"

redis_clients: dict[str, aioredis.Redis | None] = {
    "fastapi": None,
    "celery": None,
}


async def get_redis_client(pool_key: str) -> aioredis.Redis:
    if redis_clients[pool_key] is None:
        redis_clients[pool_key] = aioredis.from_url(
            REDIS_MESSAGING_URL, decode_responses=True
        )

    return redis_clients[pool_key]


async def close_redis(client_name: str):
    client = redis_clients.get(client_name, None)
    if client:
        redis_clients[client_name] = None
