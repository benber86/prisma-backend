from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.logger import get_logger
from api.models.common import Denomination
from api.routes.v1.rest.trove_managers.crud import (
    get_collateral_histogram,
    get_debt_histogram,
    get_global_collateral_ratio,
    get_health_overview,
    get_historical_collateral_ratios,
    get_historical_collateral_usd,
    get_large_positions,
    get_open_troves_overview,
)
from api.routes.v1.rest.trove_managers.models import (
    CollateralRatioDistributionResponse,
    CollateralVsDebt,
    DistributionResponse,
    FilterSet,
    HistoricalOpenedTrovesResponse,
    HistoricalTroveManagerData,
    HistoricalTroveOverviewResponse,
    LargePositionsResponse,
)
from database.queries.trove_manager import get_manager_id_by_address_and_chain
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


@router.get(
    "/{chain}/{manager}/histograms",
    response_model=DistributionResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Returns the distribution of troves across collateral value ranges"
        )
    ),
)
async def get_collateral_distribution(
    chain: str, manager: str, denomination: CollateralVsDebt = Depends()
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    manager_id = await get_manager_id_by_address_and_chain(
        chain_id=CHAINS[chain], address=manager
    )
    if not manager_id:
        raise HTTPException(status_code=404, detail="Manager not found")
    if denomination.unit == Denomination.collateral.value:
        return await (get_collateral_histogram(manager_id))
    else:
        return await (get_debt_histogram(manager_id))


@router.get(
    "/{chain}/{manager}/large_positions",
    response_model=LargePositionsResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Returns the 5 largest positions vs rest of troves"
        )
    ),
)
async def get_top_positions(
    chain: str, manager: str, denomination: CollateralVsDebt = Depends()
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    manager_id = await get_manager_id_by_address_and_chain(
        chain_id=CHAINS[chain], address=manager
    )
    if not manager_id:
        raise HTTPException(status_code=404, detail="Manager not found")
    return await (get_large_positions(manager_id, 5, denomination))
