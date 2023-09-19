from sqlalchemy import select

from database.engine import db
from database.models.troves import Collateral


async def get_collateral_id_by_chain_and_address(
    chain_id: int, address: str
) -> int | None:
    query = select([Collateral.id]).where(
        (Collateral.chain_id == chain_id) & (Collateral.address == address)
    )
    result = await db.fetch_one(query)

    if result:
        return result["id"]
    return None


async def get_collateral_address_by_id(collateral_id: int) -> str | None:
    query = select([Collateral.address]).where(Collateral.id == collateral_id)
    result = await db.fetch_one(query)

    if result:
        return result["address"]
    return None
