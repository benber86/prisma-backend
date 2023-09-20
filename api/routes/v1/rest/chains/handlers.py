from fastapi import APIRouter

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.logger import get_logger
from api.routes.v1.rest.chains.models import ChainsResponse
from utils.const import CHAINS

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=ChainsResponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get all supported chains")
    ),
)
async def get_chains():
    return ChainsResponse(data=[chain for chain in CHAINS.keys()])
