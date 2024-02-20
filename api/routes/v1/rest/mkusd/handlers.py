import json

from fastapi import APIRouter, Depends, HTTPException
from web3 import Web3

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.models.common import DecimalLabelledSeries
from api.routes.v1.rest.mkusd.crud import (
    get_circulating_supply,
    get_price,
    get_price_histogram,
    get_price_history,
    get_supply_history,
    get_two_percent,
    get_volume,
)
from api.routes.v1.rest.mkusd.models import (
    DepthResponse,
    HistoricalSupply,
    HoldersResponse,
    PriceHistogramResponse,
    PriceResponse,
    StableInfo,
    StableInfoReponse,
)
from api.routes.v1.rest.trove_managers.models import FilterSet
from services.messaging.redis import get_redis_client
from services.prices.liquidity_depth import DEPTH_SLUG, PoolDepth
from services.prices.mkusd_holders import HOLDERS_SLUG
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
    "/{chain}/supply",
    response_model=HistoricalSupply,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get historical daily supply")
    ),
)
async def get_mkusd_supply_history(chain: str):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    chain_id = CHAINS[chain]
    return HistoricalSupply(supply=await get_supply_history(chain_id))


@router.get(
    "/{chain}/histogram",
    response_model=PriceHistogramResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get historical price range distribution"
        )
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


@router.get(
    "/{chain}/holders",
    response_model=HoldersResponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get top 5 mkusd holders")
    ),
)
async def get_mkusd_top_holders(chain: str):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    redis = await get_redis_client("fastapi")
    data = json.loads(await redis.get(f"{HOLDERS_SLUG}_{chain}"))
    return HoldersResponse(holders=[DecimalLabelledSeries(**d) for d in data])


@router.get(
    "/{chain}/depth",
    response_model=DepthResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get liquidity depth on available Curve stable pools"
        )
    ),
)
async def get_mkusd_info(chain: str):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    redis = await get_redis_client("fastapi")
    data = json.loads(await redis.get(f"{DEPTH_SLUG}_{chain}"))

    return DepthResponse(depth=[PoolDepth(**d) for d in data])


@router.get(
    "/{chain}/general",
    response_model=StableInfoReponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get general stats on mkUSD")
    ),
)
async def get_mkusd_depth(chain: str):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    redis = await get_redis_client("fastapi")
    data = json.loads(await redis.get(f"{DEPTH_SLUG}_{chain}"))
    depths = [PoolDepth(**d) for d in data]
    total_depth = await get_two_percent(depths)
    supply = await get_circulating_supply(chain)
    pools = list(set([Web3.to_checksum_address(p.address) for p in depths]))

    price = await get_price(chain)
    volume = await get_volume(chain, pools)
    res = StableInfo(
        price=price, volume=volume, supply=supply, depth=total_depth
    )
    return StableInfoReponse(info=res)
