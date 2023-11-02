from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.logger import get_logger
from api.models.common import Pagination
from api.routes.v1.rest.redemptions.crud import (
    get_aggregated_stats,
    search_redemptions,
)
from api.routes.v1.rest.redemptions.models import (
    AggregateRedemptionResponse,
    FilterSet,
    ListRedemptionResponse,
    OrderFilter,
)
from database.queries.trove_manager import get_manager_id_by_address_and_chain
from utils.const import CHAINS

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/{chain}/{manager}/summary",
    response_model=AggregateRedemptionResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get aggregated summaries of redemptions"
        )
    ),
)
async def get_redemption_stats(
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
        get_aggregated_stats(
            CHAINS[chain], manager_id, filter_set.period, filter_set.groupby
        )
    )


@router.get(
    "/{chain}/{manager}",
    response_model=ListRedemptionResponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get all redemptions for a manager")
    ),
)
async def get_all_redemptions(
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
        search_redemptions(CHAINS[chain], manager_id, pagination, order)
    )
