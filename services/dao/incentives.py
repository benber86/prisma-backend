import logging

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from database.engine import db
from database.models.common import Chain
from database.models.dao import (
    IncentiveReceiver,
    IncentiveVote,
    UserWeeklyIncentivePoints,
)
from database.utils import add_user, upsert_query
from utils.const import SUBGRAPHS
from utils.const.chains import ethereum
from utils.subgraph.query import async_grt_query
from utils.time import get_week

logger = logging.getLogger()

INCENTIVE_VOTING_QUERY = """
{
  incentiveVotes(first: 1000 orderBy: weeklyVoteIndex orderDirection: asc where: {week: %d weeklyVoteIndex_gt: %d}) {
    voter {
      id
    }
    weeklyVoteIndex
    week
    isClearance
    votes(first: 1000) {
      recipient {
        id
        address
      }
      points
    }
    blockNumber
    blockTimestamp
    transactionHash
  }
}
"""


async def set_points_to_zero(week: int, voter_id: int, chain_id: int):
    query = (
        update(UserWeeklyIncentivePoints)
        .where(
            UserWeeklyIncentivePoints.week == week,
            UserWeeklyIncentivePoints.voter_id == voter_id,
            UserWeeklyIncentivePoints.chain_id == chain_id,
        )
        .values(points=0)
    )
    await db.execute(query)


async def fetch_latest_incentive_entry(chain_id):
    query = (
        select(IncentiveVote)
        .order_by(IncentiveVote.block_timestamp.desc())
        .where(IncentiveVote.chain_id == chain_id)
        .limit(1)
    )
    return await db.fetch_one(query)


async def get_latest_db_week(chain, chain_id):
    res = await fetch_latest_incentive_entry(chain_id)
    if res:
        return res["week"]
    else:
        return 0


async def update_specific_points(
    week: int,
    voter_id: int,
    chain_id: int,
    receiver_id: int,
    additional_points: int,
):
    current_point_query = select(UserWeeklyIncentivePoints.points).where(
        UserWeeklyIncentivePoints.week == week,
        UserWeeklyIncentivePoints.voter_id == voter_id,
        UserWeeklyIncentivePoints.chain_id == chain_id,
        UserWeeklyIncentivePoints.receiver_id == receiver_id,
    )
    current_points_result = await db.fetch_one(current_point_query)
    if current_points_result:
        current_points = current_points_result["points"]
    else:
        current_points = 0

    update_query = (
        insert(UserWeeklyIncentivePoints)
        .values(
            week=week,
            voter_id=voter_id,
            chain_id=chain_id,
            receiver_id=receiver_id,
            points=additional_points,
        )
        .on_conflict_do_update(
            index_elements=["week", "voter_id", "chain_id", "receiver_id"],
            set_={"points": current_points + additional_points},
        )
    )

    await db.execute(update_query)


async def parse_incentive_data(
    chain_id: int, week: int, incentive_data: dict
) -> int:
    last_index = 0
    for incentive in incentive_data["incentiveVotes"]:
        voter = incentive["voter"]["id"]
        await add_user(voter)
        if incentive["isClearance"]:
            await set_points_to_zero(week, voter, chain_id)

        indexes = {
            "index": incentive["weeklyVoteIndex"],
            "week": week,
            "chain_id": chain_id,
            "voter_id": voter,
            "target_id": None,
        }
        data = {
            "points": 0,
            "is_clearance": incentive["isClearance"],
            "block_timestamp": incentive["blockTimestamp"],
            "block_number": incentive["blockNumber"],
            "transaction_hash": incentive["transactionHash"],
        }
        votes = incentive["votes"]
        for vote in votes:
            query = upsert_query(
                IncentiveReceiver,
                indexes={
                    "chain_id": chain_id,
                    "address": vote["recipient"]["address"],
                    "index": int(vote["recipient"]["id"]),
                },
                data={"is_active": True},
                return_columns=[IncentiveReceiver.id],
            )
            recipient_id = await db.execute(query)
            indexes["target_id"] = recipient_id
            data["points"] = int(vote["points"])
            # we update the weekly tallies
            await update_specific_points(
                week, voter, chain_id, recipient_id, int(vote["points"])
            )
            query = upsert_query(IncentiveVote, indexes, data)
            await db.execute(query)
        # if only clearance, we leave the target/weigth values null
        if not votes:
            query = upsert_query(IncentiveVote, indexes, data)
            await db.execute(query)
        last_index = incentive["weeklyVoteIndex"]
    return last_index


async def sync_incentive_votes(
    chain: str = ethereum.CHAIN_NAME, chain_id: int = ethereum.CHAIN_ID
):
    await db.execute(upsert_query(Chain, {"id": chain_id}, {"name": chain}))
    endpoint = SUBGRAPHS[chain]
    current_week = get_week(chain)
    latest_week = await get_latest_db_week(chain, chain_id)
    logger.info(f"## incentive current w {current_week}, latest {latest_week}")
    for week in range(latest_week, current_week + 1):
        for index in range(0, 10000, 1000):
            logger.info(
                f"Syncing incentive votes for week {week} with index {index}"
            )
            query = INCENTIVE_VOTING_QUERY % (week, index)
            incentive_data = await async_grt_query(
                endpoint=endpoint, query=query
            )
            if not incentive_data:
                raise Exception(
                    f"Did not receive any data from the graph on chain {chain} when query for incentives {query}"
                )
            last_processed_index = await parse_incentive_data(
                chain_id, week, incentive_data
            )
            logger.info(
                f"Total entries process in this batch {last_processed_index} : {len(incentive_data['incentiveVotes'])}"
            )
            if last_processed_index < index + 1000:
                break
