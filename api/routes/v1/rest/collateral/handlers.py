import json

from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.routes.v1.rest.collateral.crud import (
    get_market_prices,
    get_oracle_prices,
)
from api.routes.v1.rest.collateral.models import (
    CollateralPriceImpact,
    CollateralPriceImpactResponse,
    CollateralPrices,
)
from api.routes.v1.rest.trove_managers.models import FilterSet
from database.queries.collateral import get_collateral_id_by_chain_and_address
from services.messaging.redis import get_redis_client
from services.prices.collateral import COL_IMPACT_SLUG
from utils.const import CHAINS

router = APIRouter()


@router.get(
    "/{chain}/{collateral}/prices",
    response_model=CollateralPrices,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get collateral historical prices")
    ),
)
async def get_collateral_price(
    chain: str, collateral: str, filter_set: FilterSet = Depends()
):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    chain_id = CHAINS[chain]
    collateral_id = await get_collateral_id_by_chain_and_address(
        chain_id, collateral
    )
    if not collateral_id:
        raise HTTPException(status_code=404, detail="Collateral not found")
    oracle_prices = await get_oracle_prices(collateral_id, filter_set.period)
    market_prices = await get_market_prices(
        chain, collateral, filter_set.period
    )
    return CollateralPrices(market=market_prices, oracle=oracle_prices)


@router.get(
    "/{chain}/{collateral}/impact",
    response_model=CollateralPriceImpactResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get price impact for collateral at various levels"
        )
    ),
)
async def get_collateral_price_impact(chain: str, collateral: str):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    redis = await get_redis_client("fastapi")
    raw_data = await redis.get(
        f"{COL_IMPACT_SLUG}_{chain}_{collateral.lower()}"
    )
    if not raw_data:
        raise HTTPException(status_code=404, detail="Collateral not found")
    data = json.loads(raw_data)
    return CollateralPriceImpactResponse(
        impact=[CollateralPriceImpact(**entry) for entry in data]
    )
