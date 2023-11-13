from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.logger import get_logger
from api.routes.v1.rest.revenue.crud import get_rev_breakdown, get_snapshots
from api.routes.v1.rest.revenue.models import (
    PeriodFilterSet,
    RevenueBreakdownResponse,
    RevenueSnapshotsResponse,
)
from utils.const import CHAINS

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/{chain}/snapshots",
    response_model=RevenueSnapshotsResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get historical revenue snapshots & breakdown"
        )
    ),
)
async def get_revenue_snapshots(
    chain: str, filter_set: PeriodFilterSet = Depends()
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    chain_id = CHAINS[chain]
    return await get_snapshots(filter_set, chain_id)


@router.get(
    "/{chain}/breakdown",
    response_model=RevenueBreakdownResponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get all time revenue breakdown")
    ),
)
async def get_revenue_breakdown(chain: str):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    chain_id = CHAINS[chain]
    return await get_rev_breakdown(chain_id)
