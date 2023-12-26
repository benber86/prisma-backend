import asyncio
import logging

from database.engine import db, wrap_dbs
from database.models.common import Chain
from database.models.dao import TotalWeeklyWeight, UserWeeklyWeights
from database.utils import upsert_query, upsert_user
from utils.const import SUBGRAPHS
from utils.const.chains import ethereum
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()


WEEKLY_TOTAL_WEIGHTS_QUERY = """
{
  lockers {
    accountDataCount
    totalWeeklyWeights
    totalWeeklyUnlocks
  }
}"""

WEEKLY_ACCOUNT_WEIGHTS_QUERY = """
{
  accountDatas(first: 500 orderBy: index orderDirection: asc where: {index_gte: %d}){
    id
    feePct
    frozen
    weight
    accountWeeklyWeights
    accountWeeklyUnlocks
  }
}"""


async def sync_total_weights(chain: str, chain_id: int) -> int:
    logger.info(f"Syncing total weight data")
    query = WEEKLY_TOTAL_WEIGHTS_QUERY
    total_weight_data = await async_grt_query(
        endpoint=SUBGRAPHS[chain], query=query
    )
    if not total_weight_data:
        logging.warning(f"No total weight data found")
        return 0
    for i, weight in enumerate(
        total_weight_data["lockers"][0]["totalWeeklyWeights"]
    ):
        if (
            weight == "0"
            and total_weight_data["lockers"][0]["totalWeeklyUnlocks"][i] == "0"
        ):
            continue
        indexes = {"chain_id": chain_id, "week": i}
        data = {
            "weight": weight,
            "unlock": total_weight_data["lockers"][0]["totalWeeklyUnlocks"][i],
        }
        query = upsert_query(TotalWeeklyWeight, indexes, data)
        await db.execute(query)
    return total_weight_data["lockers"][0]["accountDataCount"]


async def sync_account_weight_data(
    chain: str, chain_id: int, total_accounts: int
):
    for i in range(0, total_accounts, 500):
        logging.info(f"Syncing account weight data for accounts {i} - {i+500}")
        query = WEEKLY_ACCOUNT_WEIGHTS_QUERY % i
        accounts_weight_data = await async_grt_query(
            endpoint=SUBGRAPHS[chain], query=query
        )
        if not accounts_weight_data:
            logging.warning(f"No account weight data found")
            return
        for account in accounts_weight_data["accountDatas"]:
            await upsert_user(
                account["id"],
                {
                    "latest_fee": account["feePct"],
                    "frozen_balance": account["frozen"],
                    "weight": account["weight"],
                },
            )
            for j, weight in enumerate(account["accountWeeklyWeights"]):
                if weight == "0" and account["accountWeeklyUnlocks"][j] == "0":
                    continue
                indexes = {
                    "chain_id": chain_id,
                    "user_id": account["id"],
                    "week": j,
                }
                data = {
                    "weight": weight,
                    "unlock": account["accountWeeklyUnlocks"][j],
                }
                query = upsert_query(UserWeeklyWeights, indexes, data)
                await db.execute(query)


async def sync_weight_data(
    chain: str = ethereum.CHAIN_NAME, chain_id: int = ethereum.CHAIN_ID
):
    await db.execute(upsert_query(Chain, {"id": chain_id}, {"name": chain}))
    total_accounts = await sync_total_weights(chain, chain_id)
    await sync_account_weight_data(chain, chain_id, total_accounts)


if __name__ == "__main__":
    asyncio.run(wrap_dbs(sync_weight_data)("ethereum", 1))
