from sqlalchemy import desc, select

from database.engine import db
from database.models.troves import PriceRecord


async def get_latest_price_record_timestamp(collateral_id: int) -> int | None:
    query = (
        select([PriceRecord.block_timestamp])
        .where(PriceRecord.collateral_id == collateral_id)
        .order_by(desc(PriceRecord.block_timestamp))
        .limit(1)
    )
    result = await db.fetch_one(query)
    return result["block_timestamp"] if result else None
