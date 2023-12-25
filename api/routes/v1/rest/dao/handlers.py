from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.logger import get_logger
from api.models.common import Pagination
from api.routes.v1.rest.dao.crud import (
    get_boost_breakdown,
    get_delegation_users,
    get_historical_fee_accrued,
    get_top_delegation_users,
    get_user_incentives,
    get_user_ownership_votes,
    get_user_votes,
    get_weekly_boost_use,
    search_ownership_proposals,
)
from api.routes.v1.rest.dao.models import (
    DelegationUserResponse,
    HistoricalBoostFees,
    OrderFilter,
    OwnershipProposalDetailResponse,
    UserOwnershipVote,
    UserOwnershipVoteResponse,
    UserVoteResponse,
    WeeklyBoostUsage,
    WeeklyClaimDataResponse,
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
    "/{chain}/ownership/history/{user}",
    response_model=UserOwnershipVoteResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get all a user's ownership vote history details"
        )
    ),
)
async def get_user_ownership_vote_history(
    chain: str,
    user: str,
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (get_user_ownership_votes(CHAINS[chain], chain, user))


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
        BaseMethodDescription(
            summary="Get all a user's incentive vote history details"
        )
    ),
)
async def get_user_incentive_vote_history(
    chain: str,
    user: str,
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (get_user_votes(CHAINS[chain], chain, user))


@router.get(
    "/{chain}/boost/breakdown/{user}",
    response_model=WeeklyClaimDataResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get how much emissions a user was eligible for, how much was claimed by them or 3rd party and left over amount"
        )
    ),
)
async def get_user_claims_breakdown(
    chain: str,
    user: str,
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (get_boost_breakdown(CHAINS[chain], user))


@router.get(
    "/{chain}/boost/usage/{week}/{user}",
    response_model=WeeklyBoostUsage,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Shows how much of a user's weekly share of emissions was claimed over time"
        )
    ),
)
async def get_user_boost_usage(
    chain: str,
    week: int,
    user: str,
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (get_weekly_boost_use(CHAINS[chain], week, user))


@router.get(
    "/{chain}/boost/fees/{user}",
    response_model=HistoricalBoostFees,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Gets the historical amount of fees accrued over time from boost delegation for a user"
        )
    ),
)
async def get_user_boost_fees(
    chain: str,
    user: str,
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    data = await (get_historical_fee_accrued(CHAINS[chain], user))
    return HistoricalBoostFees(boost=data)


@router.get(
    "/{chain}/boost/delegations/{user}",
    response_model=DelegationUserResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Gets all the addresses that have used a user's delegation and the fees they generated"
        )
    ),
)
async def get_user_boost_users(
    chain: str,
    user: str,
):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (get_delegation_users(CHAINS[chain], user))


@router.get(
    "/{chain}/boost/fees/top/{week}/{top}",
    response_model=DelegationUserResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Gets the top X addresses by boost fees received on a given week"
        )
    ),
)
async def get_top_boost_fees(chain: str, top: int, week: int):

    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    return await (get_top_delegation_users(CHAINS[chain], top, week))
