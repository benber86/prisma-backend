from sqlalchemy import desc, select

from database.engine import db
from database.models.common import RevenueSnapshot


async def get_latest_revenue_snapshot_timestamp(chain_id: int) -> int | None:
    query = (
        select([RevenueSnapshot.timestamp])
        .where(RevenueSnapshot.chain_id == chain_id)
        .order_by(desc(RevenueSnapshot.timestamp))
        .limit(1)
    )
    result = await db.fetch_one(query)
    return result["timestamp"] if result else None
