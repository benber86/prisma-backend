from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.logger import get_logger
from api.routes.v1.rest.redemptions.crud import get_aggregated_stats
from api.routes.v1.rest.redemptions.models import (
    AggregateRedemptionResponse,
    FilterSet,
)
from utils.const import CHAINS

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/{chain}/summary",
    response_model=AggregateRedemptionResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get aggregated summaries of redemptions"
        )
    ),
)
async def get_redemption_stats(chain: str, filter_set: FilterSet = Depends()):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (
        get_aggregated_stats(
            CHAINS[chain], filter_set.period, filter_set.groupby
        )
    )
