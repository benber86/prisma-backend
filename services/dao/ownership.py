import json
import logging

from sqlalchemy import select

from database.engine import db
from database.models.common import Chain
from database.models.dao import OwnershipProposal, OwnershipVote
from database.utils import add_user, upsert_query
from services.dao.decoding import decode_payload
from utils.const import SUBGRAPHS
from utils.const.chains import ethereum
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()

OWNERSHIP_PROPOSAL_QUERY = """
{
  ownershipProposals(first: 1000 where:{index_gte: %d} orderBy: index orderDirection: desc) {
    id
    creator {
      id
    }
    status
    index
    payload {
      target
      data
    }
    week
    requiredWeight
    receivedWeight
    canExecuteAfter
    voteCount
    execution {
      transactionHash
    }
    blockNumber
    blockTimestamp
    transactionHash
    votes(first: 1000 orderBy: index orderDirection: desc) {
      id
      voter {
        id
      }
      index
      weight
      accountWeight
      decisive
      blockNumber
      blockTimestamp
      transactionHash
    }
  }
}
"""


async def get_existing_proposal_entry(chain_id: int, index: int):
    query = select(OwnershipProposal).where(
        OwnershipProposal.chain_id == chain_id,
        OwnershipProposal.index == index,
    )
    return await db.fetch_one(query)


def _str_to_proposal_status_enum(
    status: str,
) -> OwnershipProposal.OwnershipProposalStatus:
    status_mapping = {
        "notPassed": OwnershipProposal.OwnershipProposalStatus.not_passed,
        "passed": OwnershipProposal.OwnershipProposalStatus.passed,
        "cancelled": OwnershipProposal.OwnershipProposalStatus.cancelled,
        "executed": OwnershipProposal.OwnershipProposalStatus.executed,
    }

    if status not in status_mapping:
        raise Exception(f"Unknown trove status: {status}")

    return status_mapping[status]


async def sync_ownership_proposals_and_votes(
    chain: str = ethereum.CHAIN_NAME, chain_id: int = ethereum.CHAIN_ID
):
    await db.execute(upsert_query(Chain, {"id": chain_id}, {"name": chain}))
    endpoint = SUBGRAPHS[chain]
    for index in range(0, 10000, 1000):
        query = OWNERSHIP_PROPOSAL_QUERY % index
        logger.info(f"Updating ownership proposals from index: {index}")
        prop_data = await async_grt_query(endpoint=endpoint, query=query)
        if not prop_data:
            raise Exception(
                f"Did not receive any data from the graph on chain {chain} when query for ownership proposals {query}"
            )

        for proposal in prop_data["ownershipProposals"]:
            indexes = {
                "chain_id": chain_id,
                "creator_id": proposal["creator"]["id"],
                "index": proposal["index"],
            }
            await add_user(proposal["creator"]["id"])
            data = {
                "required_weight": proposal["requiredWeight"],
                "received_weight": proposal["receivedWeight"],
                "can_execute_after": int(proposal["canExecuteAfter"]),
                "vote_count": int(proposal["voteCount"]),
                "execution_tx": proposal["execution"]["transactionHash"],
                "data": proposal["payload"],
                "week": int(proposal["week"]),
                "status": _str_to_proposal_status_enum(proposal["status"]),
                "block_timestamp": proposal["blockTimestamp"],
                "block_number": proposal["blockNumber"],
                "transaction_hash": proposal["transactionHash"],
            }
            proposal_db_entry = await get_existing_proposal_entry(
                chain_id, proposal["index"]
            )

            if proposal_db_entry and not proposal_db_entry["decode_data"]:
                logger.info(
                    f"Undecoded proposal found for proposal {index}, decoding"
                )
                decode_data = decode_payload(proposal["payload"])
                if decode_data:
                    data["decode_data"] = decode_data
            query = upsert_query(
                OwnershipProposal, indexes, data, [OwnershipProposal.id]
            )
            proposal_id = await db.execute(query)

            if proposal_db_entry and proposal_db_entry["vote_count"]:
                if proposal_db_entry["vote_count"] == proposal["voteCount"]:
                    continue

            for vote in proposal["votes"]:
                indexes = {
                    "proposal_id": proposal_id,
                    "voter_id": vote["voter"]["id"],
                    "index": int(vote["index"]),
                }
                await add_user(vote["voter"]["id"])
                data = {
                    "weight": int(vote["weight"]),
                    "account_weight": vote["accountWeight"],
                    "decisive": vote["decisive"],
                    "block_timestamp": vote["blockTimestamp"],
                    "block_number": vote["blockNumber"],
                    "transaction_hash": vote["transactionHash"],
                }
                query = upsert_query(OwnershipVote, indexes, data)
                await db.execute(query)

        # no need to continue query if we reached limit
        if (
            len(prop_data["ownershipProposals"]) > 0
            and int(prop_data["ownershipProposals"][0]["id"]) < index + 1000
        ):
            break
