from functools import wraps

import databases

from settings.config import settings

db = databases.Database(settings.pg_conn_str(), min_size=5, max_size=50)


def in_db_engine(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        try:
            await db.connect()
            res = await func(*args, **kwargs)
        finally:
            await db.disconnect()
        return res

    return wrapped
