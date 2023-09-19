from api.fastapi import compile_routers
from api.routes.v1.chains.handlers import router as chains_router
from api.routes.v1.websocket.handler import router as ws_router

http_routers = [
    {"router": chains_router, "tags": ["chains"], "prefix": "/chains"},
]

ws_routers = [
    {"router": ws_router, "tags": [], "prefix": "/prisma"},
]

compiled_routers = compile_routers(
    routers=http_routers + ws_routers, root_prefix="/v1"
)
