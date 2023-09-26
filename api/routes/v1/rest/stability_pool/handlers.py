from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.routes.v1.rest.stability_pool.crud import (
    get_deposit_histogram,
    get_main_stable_deposits_withdrawals,
    get_pool_amounts,
    get_stable_deposits_and_withdrawals,
)
from api.routes.v1.rest.stability_pool.models import (
    DistributionResponse,
    PoolCumulativeWithdrawalResponse,
    PoolDepositResponse,
    PoolDepositsWithdrawalsHistorical,
    PoolStableTopResponse,
)
from api.routes.v1.rest.trove_managers.models import FilterSet
from utils.const import CHAINS

router = APIRouter()


@router.get(
    "/{chain}/deposits",
    response_model=PoolDepositResponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get historical stability pool balance")
    ),
)
async def get_collateral_price(chain: str, filter_set: FilterSet = Depends()):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    chain_id = CHAINS[chain]
    return PoolDepositResponse(
        deposits=await get_pool_amounts(chain_id, filter_set.period, False)
    )


@router.get(
    "/{chain}/cumulative_withdrawals",
    response_model=PoolCumulativeWithdrawalResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get historical cumulative USD value of collateral withdrawn from the stability pool"
        )
    ),
)
async def get_withdrawals(chain: str, filter_set: FilterSet = Depends()):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    chain_id = CHAINS[chain]
    return PoolCumulativeWithdrawalResponse(
        withdrawals=await get_pool_amounts(chain_id, filter_set.period, True)
    )


@router.get(
    "/{chain}/top/stable_withdrawals",
    response_model=PoolStableTopResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get top 10 stable withdrawals from stability pool"
        )
    ),
)
async def get_stable_withdrawals(
    chain: str, top: int, filter_set: FilterSet = Depends()
):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    chain_id = CHAINS[chain]
    return PoolStableTopResponse(
        operations=await get_main_stable_deposits_withdrawals(
            chain_id, top, filter_set.period, True
        )
    )


@router.get(
    "/{chain}/top/stable_deposits",
    response_model=PoolStableTopResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get top 10 stable deposits to stability pool"
        )
    ),
)
async def get_stable_deposits(
    chain: str, top: int, filter_set: FilterSet = Depends()
):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    chain_id = CHAINS[chain]
    return PoolStableTopResponse(
        operations=await get_main_stable_deposits_withdrawals(
            chain_id, top, filter_set.period, False
        )
    )


@router.get(
    "/{chain}/stable_operations",
    response_model=PoolDepositsWithdrawalsHistorical,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get historical stable deposits and withdrawals"
        )
    ),
)
async def get_stable_operations(chain: str, filter_set: FilterSet = Depends()):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    chain_id = CHAINS[chain]
    return await get_stable_deposits_and_withdrawals(
        chain_id, filter_set.period
    )


@router.get(
    "/{chain}/histogram/deposits",
    response_model=DistributionResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get distribution of stability pool deposits"
        )
    ),
)
async def get_stable_distribution(chain: str):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    chain_id = CHAINS[chain]
    return await get_deposit_histogram(chain_id)
