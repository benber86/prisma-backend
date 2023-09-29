from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.routes.v1.rest.mkusd.crud import (
    get_price_histogram,
    get_price_history,
)
from api.routes.v1.rest.mkusd.models import (
    PriceHistogramResponse,
    PriceResponse,
)
from api.routes.v1.rest.trove_managers.models import FilterSet
from utils.const import CHAINS

router = APIRouter()


@router.get(
    "/{chain}/history",
    response_model=PriceResponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get historical hourly prices")
    ),
)
async def get_mkusd_price_history(
    chain: str, filter_set: FilterSet = Depends()
):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    chain_id = CHAINS[chain]
    return PriceResponse(
        prices=await get_price_history(chain_id, filter_set.period)
    )


@router.get(
    "/{chain}/histogram",
    response_model=PriceHistogramResponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get historical hourly prices")
    ),
)
async def get_mkusd_price_distribution(
    chain: str, bins: int, filter_set: FilterSet = Depends()
):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    if bins < 1 or bins > 100:
        raise HTTPException(status_code=403, detail="Invalid bin count")
    chain_id = CHAINS[chain]
    return PriceHistogramResponse(
        histogram=await get_price_histogram(chain_id, bins, filter_set.period)
    )
