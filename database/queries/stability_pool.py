from sqlalchemy import select

from database.engine import db
from database.models.troves import StabilityPool


async def get_stability_pool_id_by_chain_id(chain_id: int) -> int | None:
    query = select([StabilityPool.id]).where(
        StabilityPool.chain_id == chain_id
    )
    result = await db.fetch_one(query)

    if result:
        return result["id"]
    return None
