from sqlalchemy import select

from database.engine import db
from database.models.troves import TroveManager


async def get_manager_address_by_id_and_chain(
    chain_id: int, manager_id: int
) -> str | None:
    query = select([TroveManager.address]).where(
        (TroveManager.id == manager_id) & (TroveManager.chain_id == chain_id)
    )
    result = await db.fetch_one(query)
    if result:
        return result["address"]
    return None


async def get_manager_id_by_address_and_chain(
    chain_id: int, address: str
) -> int | None:
    query = select([TroveManager.id]).where(
        (TroveManager.address.ilike(address))
        & (TroveManager.chain_id == chain_id)
    )
    result = await db.fetch_one(query)
    if result:
        return result["id"]
    return None
