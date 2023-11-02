from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.logger import get_logger
from api.models.common import Pagination
from api.routes.v1.rest.liquidations.crud import (
    get_aggregated_liquidation_stats,
    search_liquidations,
)
from api.routes.v1.rest.liquidations.models import (
    AggregateLiquidationResponse,
    FilterSet,
    ListLiquidationResponse,
    OrderFilter,
)
from database.queries.trove_manager import get_manager_id_by_address_and_chain
from utils.const import CHAINS

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/{chain}/{manager}/summary",
    response_model=AggregateLiquidationResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get aggregated summaries of liquidations"
        )
    ),
)
async def get_liquidation_stats(
    chain: str, manager: str, filter_set: FilterSet = Depends()
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    manager_id = await get_manager_id_by_address_and_chain(
        chain_id=CHAINS[chain], address=manager
    )
    if not manager_id:
        raise HTTPException(status_code=404, detail="Manager not found")

    return await (
        get_aggregated_liquidation_stats(CHAINS[chain], manager_id, filter_set)
    )


@router.get(
    "/{chain}/{manager}",
    response_model=ListLiquidationResponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get all liquidations for a manager")
    ),
)
async def get_all_liquidations(
    chain: str,
    manager: str,
    pagination: Pagination = Depends(),
    order: OrderFilter = Depends(),
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    manager_id = await get_manager_id_by_address_and_chain(
        chain_id=CHAINS[chain], address=manager
    )
    if not manager_id:
        raise HTTPException(status_code=404, detail="Manager not found")

    return await (
        search_liquidations(CHAINS[chain], manager_id, pagination, order)
    )


@router.get(
    "/{chain}",
    response_model=ListLiquidationResponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get all liquidations for a chain")
    ),
)
async def get_all_chain_liquidations(
    chain: str,
    pagination: Pagination = Depends(),
    order: OrderFilter = Depends(),
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (search_liquidations(CHAINS[chain], None, pagination, order))
