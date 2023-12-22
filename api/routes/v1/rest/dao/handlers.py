from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.logger import get_logger
from api.models.common import Pagination
from api.routes.v1.rest.dao.crud import (
    get_user_incentives,
    get_user_votes,
    search_ownership_proposals,
)
from api.routes.v1.rest.dao.models import (
    OrderFilter,
    OwnershipProposalDetailResponse,
    UserVoteResponse,
    WeeklyUserVoteDataResponse,
)
from utils.const import CHAINS

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/{chain}/ownership/proposals",
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


@router.get(
    "/{chain}/incentives/distribution/{user}",
    response_model=WeeklyUserVoteDataResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get how a user distributed their points on all weeks"
        )
    ),
)
async def get_user_incentive_distrib(
    chain: str,
    user: str,
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (get_user_incentives(CHAINS[chain], chain, user))


@router.get(
    "/{chain}/incentives/history/{user}",
    response_model=UserVoteResponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get all a user's vote history details")
    ),
)
async def get_user_incentive_vote_history(
    chain: str,
    user: str,
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (get_user_votes(CHAINS[chain], chain, user))
