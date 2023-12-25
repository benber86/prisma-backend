import asyncio
import logging

from sqlalchemy import and_, func, select, update
from sqlalchemy.dialects.postgresql import insert

from database.engine import db, wrap_dbs
from database.models.common import Chain
from database.models.dao import (
    BatchRewardClaim,
    WeeklyBoostData,
    WeeklyEmissions,
)
from database.utils import add_user, upsert_query
from utils.const import SUBGRAPHS
from utils.const.chains import ethereum
from utils.subgraph.query import async_grt_query
from utils.time import get_week

logger = logging.getLogger()


async def fetch_latest_weekly_boost_data(chain_id):
    query = (
        select(WeeklyBoostData)
        .order_by(WeeklyBoostData.week.desc())
        .where(WeeklyBoostData.chain_id == chain_id)
        .limit(1)
    )
    return await db.fetch_one(query)


async def get_latest_db_week(chain_id):
    res = await fetch_latest_weekly_boost_data(chain_id)
    if res:
        return res["week"]
    else:
        return 0


WEEKLY_BOOST_DATA_QUERY = """
{
  weeklyBoostDatas(first:1000 skip: %d orderBy:index orderDirection: desc where:{week: %d}) {
    index
    account {
      id
    }
    week
    boost
    pct
    lastAppliedFee
    nonLockingFee
    boost
    boostDelegation
    boostDelegationUsers

    eligibleFor
    totalClaimed
    selfClaimed
    otherClaimed
    accruedFees
    timeToDepletion
    batchRewardClaims(first:1000 orderBy:index orderDirection: desc) {
      caller{
        id
      }
      receiver {
        id
      }
      boostDelegate {
        id
      }
      index
      totalClaimed
      totalClaimedBoosted
      delegateRemainingEligible
      maxFee
      week
      feeGenerated
      feeApplied
      blockNumber
      blockTimestamp
      transactionHash
    }
  }
}"""

WEEKLY_EMISSIONS_QUERY = """
{
  weeklyEmissions(where: {week_gte: %d week_lte: %d}) {
    week
    emissions
  }
}
"""

EXTENDED_CLAIM_QUERY = """
{
  batchRewardClaims(first:1000 orderBy:index orderDirection: desc where: {boostDelegate: "%s" week: %d index_lte: %d}) {
      caller{
        id
      }
      receiver {
        id
      }
      boostDelegate {
        id
      }
      index
      totalClaimed
      totalClaimedBoosted
      delegateRemainingEligible
      maxFee
      week
      feeGenerated
      feeApplied
      blockNumber
      blockTimestamp
      transactionHash
    }
}
"""


async def update_emission_data(
    chain: str, chain_id: int, latest_week: int, current_week: int
):
    logger.info(
        f"Syncing emissions data for week {latest_week} to {current_week}"
    )
    query = WEEKLY_EMISSIONS_QUERY % (latest_week, current_week)
    emission_data = await async_grt_query(
        endpoint=SUBGRAPHS[chain], query=query
    )
    if not emission_data:
        logging.warning(f"No emission data found")
        return
    for em in emission_data["weeklyEmissions"]:
        indexes = {"chain_id": chain_id, "week": em["week"]}
        data = {"emissions": em["emissions"]}
        query = upsert_query(WeeklyEmissions, indexes, data)
        await db.execute(query)


async def add_claim_data(
    chain: str,
    chain_id: int,
    week: int,
    delegate: str,
    delegation_count: int,
    data_batch: dict[str, list],
):
    while True:
        for claim_data in data_batch["batchRewardClaims"]:

            await add_user(claim_data["caller"]["id"])
            await add_user(claim_data["receiver"]["id"])
            await add_user(claim_data["boostDelegate"]["id"])
            indexes = {
                "week": claim_data["week"],
                "chain_id": chain_id,
                "caller_id": claim_data["caller"]["id"],
                "delegate_id": claim_data["boostDelegate"]["id"],
                "index": claim_data["index"],
            }
            data = {
                "receiver_id": claim_data["receiver"]["id"],
                "total_claimed": claim_data["totalClaimed"],
                "total_claimed_boosted": claim_data["totalClaimedBoosted"],
                "delegate_remaining_eligible": claim_data[
                    "delegateRemainingEligible"
                ],
                "max_fee": claim_data["maxFee"],
                "fee_generated": claim_data["feeGenerated"],
                "fee_applied": claim_data["feeApplied"],
                "block_number": claim_data["blockNumber"],
                "block_timestamp": claim_data["blockTimestamp"],
                "transaction_hash": claim_data["transactionHash"],
            }
            db_query = upsert_query(BatchRewardClaim, indexes, data)
            await db.execute(db_query)
        return
        if delegation_count < 1000:
            return
        logger.info(
            f"Found more than 1000 delegation for delegate {delegate} on week {week}, processing {delegation_count} to {delegation_count - 1000}"
        )
        delegation_count -= 1000
        query = EXTENDED_CLAIM_QUERY % (delegate, week, delegation_count)
        data_batch = await async_grt_query(
            endpoint=SUBGRAPHS[chain], query=query
        )


async def sync_weekly_boost_data(chain: str, chain_id: int, week: int):
    for i in range(0, 6000, 1000):
        logger.info(f"Syncing weekly boost data for week {week}")
        query = WEEKLY_BOOST_DATA_QUERY % (i, week)
        boost_data = await async_grt_query(
            endpoint=SUBGRAPHS[chain], query=query
        )
        if not boost_data:
            logger.info(f"No boost data found for week {week}")
            return

        for boost in boost_data["weeklyBoostDatas"]:
            await add_user(boost["account"]["id"])
            indexes = {
                "chain_id": chain_id,
                "user_id": boost["account"]["id"],
                "week": boost["week"],
            }
            data = {
                "boost": boost["boost"],
                "pct": boost["pct"],
                "last_applied_fee": boost["lastAppliedFee"],
                "boost_delegation": boost["boostDelegation"],
                "boost_delegation_users": boost["boostDelegationUsers"],
                "eligible_for": boost["eligibleFor"],
                "total_claimed": boost["totalClaimed"],
                "self_claimed": boost["selfClaimed"],
                "other_claimed": boost["otherClaimed"],
                "accrued_fees": boost["accruedFees"],
                "time_to_depletion": boost["timeToDepletion"],
            }
            query = upsert_query(WeeklyBoostData, indexes, data)
            await db.execute(query)
            await add_claim_data(
                chain,
                chain_id,
                week,
                boost["account"]["id"],
                boost["boostDelegationUsers"],
                boost,
            )


async def sync_boost_data(
    chain: str = ethereum.CHAIN_NAME, chain_id: int = ethereum.CHAIN_ID
):
    await db.execute(upsert_query(Chain, {"id": chain_id}, {"name": chain}))
    current_week = get_week(chain)
    latest_week = await get_latest_db_week(chain_id)
    logger.debug(
        f"## Boost data current w {current_week}, latest {latest_week}"
    )
    await update_emission_data(chain, chain_id, latest_week, current_week)
    for week in range(latest_week, current_week + 1):
        await sync_weekly_boost_data(chain, chain_id, week)


if __name__ == "__main__":
    asyncio.run(wrap_dbs(sync_boost_data)("ethereum", 1))
