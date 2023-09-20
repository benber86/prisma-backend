from functools import wraps

import databases

from services.messaging.redis import close_redis_pool, get_redis_pool
from settings.config import settings

db = databases.Database(settings.pg_conn_str(), min_size=5, max_size=50)


def wrap_dbs(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        try:
            await get_redis_pool("celery")
            await db.connect()
            res = await func(*args, **kwargs)
        finally:
            await db.disconnect()
            await close_redis_pool("celery")
        return res

    return wrapped
