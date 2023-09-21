from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.logger import get_logger
from api.routes.v1.rest.trove_managers.crud import (
    get_global_collateral_ratio,
    get_health_overview,
    get_historical_collateral_ratios,
    get_historical_collateral_usd,
    get_open_troves_overview,
)
from api.routes.v1.rest.trove_managers.models import (
    CollateralRatioDistributionResponse,
    FilterSet,
    HistoricalOpenedTrovesResponse,
    HistoricalTroveManagerData,
    HistoricalTroveOverviewResponse,
)
from utils.const import CHAINS

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/{chain}/collateral_ratios",
    response_model=HistoricalTroveOverviewResponse,
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
    response_model=HistoricalTroveManagerData,
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


@router.get(
    "/{chain}/open_troves",
    response_model=HistoricalOpenedTrovesResponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get historical number of open troves")
    ),
)
async def get_historical_open_troves(
    chain: str, filter_set: FilterSet = Depends()
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (get_open_troves_overview(CHAINS[chain], filter_set.period))


@router.get(
    "/{chain}/ratio_distribution",
    response_model=CollateralRatioDistributionResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get debt distribution across CR deciles"
        )
    ),
)
async def get_cr_deciles_overview(chain: str):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (get_health_overview(CHAINS[chain]))


@router.get(
    "/{chain}/collateral",
    response_model=HistoricalTroveOverviewResponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get collateral amounts across vaults")
    ),
)
async def get_collateral_overview(
    chain: str, filter_set: FilterSet = Depends()
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (
        get_historical_collateral_usd(CHAINS[chain], filter_set.period)
    )
