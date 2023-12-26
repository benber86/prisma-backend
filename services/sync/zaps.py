import logging

from database.engine import db
from database.models.troves import ZapStakes
from database.queries.collateral import get_collateral_id_by_chain_and_address
from database.utils import upsert_query
from services.celery import celery
from utils.const import SUBGRAPHS
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()

ZAP_STAKES_QUERY = """

{
  zapStakes(first: 1000 orderBy:index orderDirection: desc where: {index_gte: %d}) {
    ethAmount
    collateral{
      id
    }
    index
    blockNumber
    blockTimestamp
    transactionHash
  }
}
"""


async def update_zap_records(chain: str, chain_id: int):
    endpoint = SUBGRAPHS[chain]
    index = 0
    logger.info("Syncing zap stake data")
    for i in range(0, 11000, 1000):
        query = ZAP_STAKES_QUERY % i
        zap_data = await async_grt_query(endpoint=endpoint, query=query)
        if not zap_data:
            raise Exception(
                f"Unable to retrieve zap data from the graph {query}"
            )
        for zap in zap_data["zapStakes"]:
            collateral_id = await get_collateral_id_by_chain_and_address(
                chain_id, zap["collateral"]["id"]
            )
            index = zap["index"]
            index_data = {
                "collateral_id": collateral_id,
                "index": index,
                "block_timestamp": zap["blockTimestamp"],
            }
            data = {
                "amount": zap["ethAmount"],
                "block_number": zap["blockNumber"],
                "transaction_hash": zap["transactionHash"],
            }
            query = upsert_query(ZapStakes, index_data, data)
            await db.execute(query)

    if index == 0:
        return
