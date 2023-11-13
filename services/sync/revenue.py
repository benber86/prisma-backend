import asyncio
import logging

from database.engine import db, wrap_dbs
from database.models.common import RevenueSnapshot
from database.queries.revenue_snapshots import (
    get_latest_revenue_snapshot_timestamp,
)
from database.utils import upsert_query
from services.celery import celery
from utils.const import CHAINS, SUBGRAPHS
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()

REVENUE_QUERY = """

{
  revenueSnapshots(first: 1000 where: {timestamp_gte: %d} orderBy: timestamp orderDirection: desc) {
    unlockPenaltyRevenueUSD
    borrowingFeesRevenueUSD
    redemptionFeesRevenueUSD
    timestamp
  }
}

"""


@celery.task
def update_revenue_snapshots(chain: str, chain_id: int):
    asyncio.run(wrap_dbs(get_revenue_snapshots)(chain, chain_id))


async def get_revenue_snapshots(chain: str, chain_id: int):
    endpoint = SUBGRAPHS[chain]
    last_timestamp = await get_latest_revenue_snapshot_timestamp(chain_id)
    if not last_timestamp:
        last_timestamp = 0

    query = REVENUE_QUERY % last_timestamp
    snapshots_data = await async_grt_query(endpoint=endpoint, query=query)
    if not snapshots_data:
        raise Exception(
            f"Unable to retrieve revenue snapshots data from the graph {query}"
        )

    for record in snapshots_data["revenueSnapshots"]:
        index = {
            "chain_id": chain_id,
            "timestamp": int(record["timestamp"]),
        }
        data = {
            "unlock_penalty_revenue_usd": record["unlockPenaltyRevenueUSD"],
            "borrowing_fees_revenue_usd": record["borrowingFeesRevenueUSD"],
            "redemption_fees_revenue_usd": record["redemptionFeesRevenueUSD"],
        }
        query = upsert_query(RevenueSnapshot, index, data)
        await db.execute(query)
