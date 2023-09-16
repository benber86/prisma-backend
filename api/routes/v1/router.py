from api.fastapi import compile_routers
from api.routes.v1.chains.handlers import router as chains_router

http_routers = [
    {"router": chains_router, "tags": ["chains"], "prefix": "/chains"},
]

compiled_routers = compile_routers(routers=http_routers, root_prefix="/v1")
