import asyncpg

from settings.config import settings


class PostgresNotificationPool:
    async def create_pool(self):
        self.pool = await asyncpg.create_pool(dsn=settings.pg_conn_str())

    async def close_pool(self):
        await self.pool.close()


pg_notify_pool = PostgresNotificationPool()
