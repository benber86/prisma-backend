from api.fastapi import compile_routers
from api.routes.v1.rest.chains.handlers import router as chains_router
from api.routes.v1.rest.collateral.handlers import router as collateral_router
from api.routes.v1.rest.mkusd.handlers import router as stablecoin_router
from api.routes.v1.rest.stability_pool.handlers import (
    router as stability_pool_router,
)
from api.routes.v1.rest.trove.handlers import router as trove_router
from api.routes.v1.rest.trove_managers.handlers import (
    router as trove_manager_router,
)
from api.routes.v1.websocket.handler import router as ws_router

http_routers = [
    {"router": chains_router, "tags": ["chains"], "prefix": "/chains"},
    {
        "router": collateral_router,
        "tags": ["collateral"],
        "prefix": "/collateral",
    },
    {
        "router": trove_manager_router,
        "tags": ["vaults"],
        "prefix": "/managers",
    },
    {
        "router": stability_pool_router,
        "tags": ["pool"],
        "prefix": "/pool",
    },
    {
        "router": stablecoin_router,
        "tags": ["mkusd"],
        "prefix": "/mkusd",
    },
    {
        "router": trove_router,
        "tags": ["trove"],
        "prefix": "/trove",
    },
]

ws_routers = [
    {"router": ws_router, "tags": [], "prefix": "/prisma"},
]

compiled_routers = compile_routers(
    routers=http_routers + ws_routers, root_prefix="/v1"
)
