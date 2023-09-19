import logging
from typing import Any

from database.engine import db
from database.models.troves import PriceRecord
from database.queries.collateral import get_collateral_address_by_id
from database.queries.price_records import get_latest_price_record_timestamp
from database.utils import upsert_query
from utils.const import SUBGRAPHS
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()

PRICE_RECORDS_QUERY = """
{
  priceRecords(first: 1000 skip: %d where:
    {blockTimestamp_gte: %d
      collateral:"%s"}
    orderBy: blockTimestamp
    orderDirection: desc) {
    price
    blockNumber
    blockTimestamp
    transactionHash
  }
}

"""


async def update_price_records(chain: str, collateral_id: int):
    endpoint = SUBGRAPHS[chain]
    last_timestamp = await get_latest_price_record_timestamp(collateral_id)
    if not last_timestamp:
        last_timestamp = 0
    collateral_address = await get_collateral_address_by_id(collateral_id)
    if not collateral_address:
        raise Exception(
            f"Could not retrieve collateral address for collateral id {collateral_id}"
        )
    # fetch the last 5000 records (or less) since last timestamp
    records: list[dict[str, Any]] = []
    for i in range(6):
        query = PRICE_RECORDS_QUERY % (
            i * 1000,
            last_timestamp,
            collateral_address.lower(),
        )
        price_data = await async_grt_query(endpoint=endpoint, query=query)
        if not price_data:
            raise Exception(
                f"Unable to retrieve price data from the graph {query}"
            )
        price_records = price_data["priceRecords"]
        if len(price_records) > 0:
            records += price_records
        else:
            break
        # if we didn't reach max capacity we can stop early
        if len(price_data) < 1000:
            break

    for record in records:
        index = {
            "collateral_id": collateral_id,
            "block_timestamp": record["blockTimestamp"],
        }
        data = {
            "block_number": record["blockNumber"],
            "transaction_hash": record["transactionHash"],
            "price": record["price"],
        }
        query = upsert_query(PriceRecord, index, data)
        await db.execute(query)
