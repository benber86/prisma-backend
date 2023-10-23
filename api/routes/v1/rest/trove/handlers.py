from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.models.common import Pagination
from api.routes.v1.rest.trove.crud import (
    get_all_snapshots,
    get_position,
    get_snapshot_historical_stats,
    get_trove_details,
    search_for_troves,
)
from api.routes.v1.rest.trove.models import (
    FilterSet,
    RatioPosition,
    TroveEntry,
    TroveEntryReponse,
    TroveHistoryResponse,
    TroveSnapshotsResponse,
)
from database.queries.trove_manager import get_manager_id_by_address_and_chain
from utils.const import CHAINS

router = APIRouter()


@router.get(
    "/{chain}/{manager}/troves",
    response_model=TroveEntryReponse,
    **get_router_method_settings(
        BaseMethodDescription(summary="List or search for troves")
    ),
)
async def get_troves(
    chain: str,
    manager: str,
    pagination: Pagination = Depends(),
    filter_set: FilterSet = Depends(),
):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    manager_id = await get_manager_id_by_address_and_chain(
        chain_id=CHAINS[chain], address=manager
    )
    if not manager_id:
        raise HTTPException(status_code=404, detail="Manager not found")

    result = await search_for_troves(manager_id, pagination, filter_set)
    if not result:
        raise HTTPException(status_code=404, detail="Data not found")
    return result


@router.get(
    "/{chain}/{manager}/snapshots/{owner}",
    response_model=TroveSnapshotsResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get all available snapshots for a specific trove"
        )
    ),
)
async def get_trove_snapshots(chain: str, manager: str, owner: str):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    manager_id = await get_manager_id_by_address_and_chain(
        chain_id=CHAINS[chain], address=manager
    )
    if not manager_id:
        raise HTTPException(status_code=404, detail="Manager not found")

    return await get_all_snapshots(manager_id, owner)


@router.get(
    "/{chain}/{manager}/history/{owner}",
    response_model=TroveHistoryResponse,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get collateral/CR/debt history for a specific trove"
        )
    ),
)
async def get_trove_values(chain: str, manager: str, owner: str):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    manager_id = await get_manager_id_by_address_and_chain(
        chain_id=CHAINS[chain], address=manager
    )
    if not manager_id:
        raise HTTPException(status_code=404, detail="Manager not found")

    return await get_snapshot_historical_stats(manager_id, owner)


@router.get(
    "/{chain}/{manager}/rank/{owner}",
    response_model=RatioPosition,
    **get_router_method_settings(
        BaseMethodDescription(
            summary="Get trove position and cumulative collateral at each ratio"
        )
    ),
)
async def get_trove_rank(chain: str, manager: str, owner: str):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    manager_id = await get_manager_id_by_address_and_chain(
        chain_id=CHAINS[chain], address=manager
    )
    if not manager_id:
        raise HTTPException(status_code=404, detail="Manager not found")

    return await get_position(manager_id, owner)


@router.get(
    "/{chain}/{manager}/{owner}",
    response_model=TroveEntry,
    **get_router_method_settings(
        BaseMethodDescription(summary="Get details for a single trove")
    ),
)
async def get_trove(chain: str, manager: str, owner: str):
    if chain not in CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    manager_id = await get_manager_id_by_address_and_chain(
        chain_id=CHAINS[chain], address=manager
    )
    if not manager_id:
        raise HTTPException(status_code=404, detail="Manager not found")

    res = await get_trove_details(manager_id, owner)
    if not res:
        raise HTTPException(
            status_code=404, detail="No data found for this trove"
        )
    return res
