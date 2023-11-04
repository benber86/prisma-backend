from fastapi import APIRouter, Depends

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.logger import get_logger
from api.routes.v1.rest.staking.crud import (
    get_aggregated_flow,
    get_aggregated_tvl,
    get_snapshots,
    get_staking_balance_histogram,
    get_user_details,
)
from api.routes.v1.rest.staking.models import (
    AggregateStakingFlowResponse,
    DistributionResponse,
    FilterSet,
    PeriodFilterSet,
    StakingSnapshotsResponse,
    StakingTvlResponse,
    UserDetails,
)

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/flow",
    response_model=AggregateStakingFlowResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get liquidity flows into staking contract"
        )
    ),
)
async def get_staking_flow(filter_set: FilterSet = Depends()):

    return await get_aggregated_flow(filter_set)


@router.get(
    "/tvl",
    response_model=StakingTvlResponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get historical TVL of staking contract")
    ),
)
async def get_staking_tvl(filter_set: FilterSet = Depends()):

    return await get_aggregated_tvl(filter_set)


@router.get(
    "/snapshots",
    response_model=StakingSnapshotsResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get historical snapshots of staking contract"
        )
    ),
)
async def get_staking_snapshots(filter_set: PeriodFilterSet = Depends()):

    return await get_snapshots(filter_set)


@router.get(
    "/{user}/details",
    response_model=UserDetails,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get the details of a user's interactions with the staking contract"
        )
    ),
)
async def get_user_info(user: str):

    return await get_user_details(user)


@router.get(
    "/distribution",
    response_model=DistributionResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get distribution of staking contract positions"
        )
    ),
)
async def get_staking_distribution():

    return await get_staking_balance_histogram()
