from fastapi import APIRouter, Depends, HTTPException

from api.fastapi import BaseMethodDescription, get_router_method_settings
from api.models.common import Pagination
from api.routes.v1.rest.trove.crud import search_for_troves
from api.routes.v1.rest.trove.models import FilterSet, TroveEntryReponse
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
