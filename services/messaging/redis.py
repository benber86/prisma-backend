import aioredis

from settings.config import settings

REDIS_MESSAGING_URL = f"redis://:{settings.REDIS_PASSWORD}@redis:6379/1"

redis_pools: dict[str, aioredis.ConnectionPool | None] = {
    "fastapi": None,
    "celery": None,
}


async def get_redis_pool(pool_key: str) -> aioredis.ConnectionPool:
    if redis_pools[pool_key] is None:
        redis_pools[pool_key] = aioredis.ConnectionPool.from_url(
            REDIS_MESSAGING_URL, decode_responses=True
        )
    return redis_pools[pool_key]


async def close_redis_pool(pool_name: str):
    if redis_pools.get(pool_name) is not None:
        await redis_pools[pool_name].disconnect()  # type: ignore
        redis_pools[pool_name] = None
