from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.logger import get_logger
from api.models.common import Pagination
from api.routes.v1.rest.dao.crud import search_ownership_proposals
from api.routes.v1.rest.dao.models import (
    OrderFilter,
    OwnershipProposalDetailResponse,
)
from utils.const import CHAINS

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/{chain}",
    response_model=OwnershipProposalDetailResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get or search all ownership proposals for a chain"
        )
    ),
)
async def get_all_ownership_proposals(
    chain: str,
    pagination: Pagination = Depends(),
    order: OrderFilter = Depends(),
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (search_ownership_proposals(CHAINS[chain], pagination, order))
