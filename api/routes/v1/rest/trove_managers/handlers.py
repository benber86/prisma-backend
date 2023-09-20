from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.logger import get_logger
from api.routes.v1.rest.trove_managers.crud import (
    get_global_collateral_ratio,
    get_historical_collateral_ratios,
)
from api.routes.v1.rest.trove_managers.models import (
    FilterSet,
    HistoricalCollateralRatioResponse,
    HistoricalTroveManagerCR,
)
from utils.const import CHAINS

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/{chain}/collateral_ratios",
    response_model=HistoricalCollateralRatioResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get historical collateral ratio of all markets"
        )
    ),
)
async def get_all_ratios(chain: str, filter_set: FilterSet = Depends()):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (
        get_historical_collateral_ratios(CHAINS[chain], filter_set.period)
    )


@router.get(
    "/{chain}/global_collateral_ratio",
    response_model=HistoricalTroveManagerCR,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get global collateral ratio")
    ),
)
async def get_global_ratio(chain: str, filter_set: FilterSet = Depends()):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (
        get_global_collateral_ratio(CHAINS[chain], filter_set.period)
    )
