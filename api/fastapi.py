import decimal
import itertools
import json
import os
from typing import Any

import orjson
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from api.logger import get_logger

logger = get_logger(__name__)


class Error(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: Error


def disable_logging():
    def decorator(func):
        func.disable_logging = True
        return func

    return decorator


@disable_logging()
def ping_endpoint():
    return PlainTextResponse("pong")


def register_routers(
    app_uri_prefix="",
    routers=(),
    on_startup=(),
    on_shutdown=(),
    ping_endpoint=ping_endpoint,
):
    if (
        app_uri_prefix
        and not app_uri_prefix.startswith("/")
        and len(app_uri_prefix) > 1
    ):
        raise ValueError(
            "app_uri_prefix should start with / and consists of more than 1 char"
        )

    app = FastAPI(
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        docs_url=f"{app_uri_prefix}/feeds-docs",
        redoc_url=f"{app_uri_prefix}/feeds-redoc",
        openapi_url=f"{app_uri_prefix}/feeds-docs/openapi.json",
        swagger_ui_oauth2_redirect_url=f"{app_uri_prefix}/feeds-docs/oauth2-redirect",
    )

    title = os.getenv("FASTAPI_TITLE", "FastAPI")
    description = os.getenv("FASTAPI_DESCRIPTION", "Price Feeds Backend API")
    app.title = title
    app.description = description

    for router_data in itertools.chain(*routers):
        app.include_router(
            router=router_data["router"],
            tags=router_data["tags"],
            prefix=app_uri_prefix + router_data["prefix"],
            dependencies=[Depends(d) for d in router_data["dependencies"]],
            responses={
                400: {"model": ErrorResponse},
                401: {"model": ErrorResponse},
                403: {"model": ErrorResponse},
                500: {"model": ErrorResponse},
            },
        )
    app.add_api_route(
        path=f"{app_uri_prefix}/ping",
        endpoint=ping_endpoint,
        tags=["Health checks"],
    )
    app.add_middleware(LoggingMiddleware)

    return app


def custom_json_encoder(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


class EnrichedORJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        try:
            assert (
                orjson is not None
            ), "orjson must be installed to use EnrichedORJSONResponse"
            return orjson.dumps(
                content,
                default=custom_json_encoder,
                option=orjson.OPT_SERIALIZE_NUMPY
                | orjson.OPT_SERIALIZE_DATACLASS,
            )
        except TypeError as e:
            if str(e) == "Integer exceeds 64-bit range":
                return json.dumps(content).encode()
            raise


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        logger.info(
            msg="Request",
            extra={
                "headers": request.headers,
                "remote_addr": request.client.host,
                "method": request.method,
                "path": request.scope["path"],
                "url": str(request.url),
                "query_params": dict(request.query_params),
            },
        )
        response = await call_next(request)
        return response


def compile_routers(routers, root_prefix: str = None, dependencies=None):
    if root_prefix and not root_prefix.startswith("/"):
        raise ValueError("root_prefix should start with /")

    compiled_routers = []
    common_dependencies = dependencies or []
    for router in routers:
        r = {**router}
        r["router"].default_response_class = EnrichedORJSONResponse

        dependencies = r.get("dependencies", [])
        dependencies.extend(common_dependencies)

        r["prefix"] = root_prefix + r["prefix"]
        r["tags"] = [
            f"{root_prefix.lstrip('/')} {tag}" if root_prefix else tag
            for tag in r["tags"] or []
        ]
        r["dependencies"] = dependencies
        compiled_routers.append(r)

    return compiled_routers


class BaseMethodDescription(BaseModel):
    summary: str
    description: str = ""


def get_router_method_settings(description: BaseMethodDescription) -> dict:
    return dict(
        response_model_exclude_unset=False,
        response_model_exclude_none=False,
        **description.dict(),
    )
