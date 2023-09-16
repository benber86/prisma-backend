import asyncio

from fastapi.middleware.cors import CORSMiddleware

from api.fastapi import register_routers
from api.logger import init_logger
from api.routes.v1.router import compiled_routers as compiled_routers_v1
from database.engine import db
from database.pool import pg_notify_pool
from settings.config import settings

init_logger(is_debug=settings.DEBUG)


async def ping():
    return {"status": "ok"}


app = register_routers(
    ping_endpoint=ping,
    routers=[compiled_routers_v1],
    app_uri_prefix=f"/{settings.APP_URI_PREFIX}"
    if settings.APP_URI_PREFIX
    else "",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_db():
    await db.connect()
    await pg_notify_pool.create_pool()


@app.on_event("shutdown")
async def shutdown_db():
    await db.disconnect()
    await asyncio.wait_for(pg_notify_pool.close_pool(), timeout=60.0)
