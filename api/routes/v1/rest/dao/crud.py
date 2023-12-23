import logging
from enum import Enum

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import aliased
from web3 import Web3

from api.models.common import Pagination
from api.routes.v1.rest.dao.models import (
    OrderFilter,
    OwnershipProposalDetail,
    OwnershipProposalDetailResponse,
    UserOwnershipVote,
    UserOwnershipVoteResponse,
    UserVote,
    UserVoteResponse,
    WeeklyUserVote,
    WeeklyUserVoteData,
    WeeklyUserVoteDataResponse,
)
from database.engine import db
from database.models.common import User
from database.models.dao import (
    IncentiveReceiver,
    IncentiveVote,
    OwnershipProposal,
    OwnershipVote,
    UserWeeklyIncentivePoints,
)
from utils.const import RECEIVER_MAPPINGS
from utils.time import get_week


async def search_ownership_proposals(
    chain_id: int,
    pagination: Pagination,
    order: OrderFilter,
) -> OwnershipProposalDetailResponse:

    query = (
        select([OwnershipProposal, User.label.label("creator_label")])
        .join(User, OwnershipProposal.creator_id == User.id)
        .where(OwnershipProposal.chain_id == chain_id)
    )

    if order.creator_filter:
        query = query.where(
            OwnershipProposal.creator_id == order.creator_filter
        )
    if order.decode_data_filter:
        query = query.where(
            OwnershipProposal.decode_data == order.decode_data_filter
        )

    order_column = getattr(OwnershipProposal, order.order_by)  # type: ignore
    if order.desc:
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column)

    items_per_page = pagination.items
    offset = (pagination.page - 1) * items_per_page
    query = query.limit(items_per_page).offset(offset)

    results = await db.fetch_all(query)
    proposals = []
    for result in results:
        result_dict = dict(result)
        result_dict["creator"] = Web3.to_checksum_address(
            result_dict["creator_id"]
        )
        if isinstance(result_dict["status"], Enum):
            result_dict["status"] = result_dict["status"].value
        proposal = OwnershipProposalDetail(**result_dict)
        proposals.append(proposal)
    return OwnershipProposalDetailResponse(proposals=proposals)


async def get_user_incentives(
    chain_id: int, chain: str, user: str
) -> WeeklyUserVoteDataResponse:
    Receiver = aliased(IncentiveReceiver)

    current_week = get_week(chain)

    query = (
        select(
            [
                UserWeeklyIncentivePoints.week,
                Receiver.index.label("receiver_id"),
                Receiver.address.label("receiver_address"),
                UserWeeklyIncentivePoints.points,
            ]
        )
        .join(Receiver, UserWeeklyIncentivePoints.receiver_id == Receiver.id)
        .where(
            UserWeeklyIncentivePoints.voter_id.ilike(user),
            UserWeeklyIncentivePoints.chain_id == chain_id,
        )
        .order_by(UserWeeklyIncentivePoints.week)
    )

    result = await db.fetch_all(query)

    weekly_votes: dict[int, list] = {}
    for row in result:
        week = row.week
        vote = WeeklyUserVote(
            receiver_id=row.receiver_id,
            receiver_address=row.receiver_address,
            receiver_label=RECEIVER_MAPPINGS[chain][row.receiver_id]
            if row.receiver_id in RECEIVER_MAPPINGS[chain]
            else row.receiver_address,
            points=row.points,
        )
        weekly_votes.setdefault(week, []).append(vote)

    latest_week_in_results = max(weekly_votes.keys(), default=0)

    if latest_week_in_results < current_week:
        for week in range(latest_week_in_results + 1, current_week + 1):
            for vote in weekly_votes.get(latest_week_in_results, []):
                padded_vote = WeeklyUserVote(
                    receiver_id=vote.receiver_id,
                    receiver_address=vote.receiver_address,
                    receiver_label=vote.receiver_label,
                    points=vote.points,
                )
                weekly_votes.setdefault(week, []).append(padded_vote)

    votes_data = [
        WeeklyUserVoteData(week=week, votes=votes)
        for week, votes in weekly_votes.items()
    ]
    return WeeklyUserVoteDataResponse(votes=votes_data)


async def get_user_votes(
    chain_id: int, chain: str, user: str
) -> UserVoteResponse:
    Receiver = aliased(IncentiveReceiver)

    query = (
        select(
            [
                IncentiveVote.index,
                Receiver.index.label("receiver_id"),
                Receiver.address.label("receiver_address"),
                IncentiveVote.week,
                IncentiveVote.points,
                IncentiveVote.is_clearance,
                IncentiveVote.block_number,
                IncentiveVote.block_timestamp,
                IncentiveVote.transaction_hash,
            ]
        )
        .join(Receiver, IncentiveVote.target_id == Receiver.id)
        .where(
            IncentiveVote.voter_id.ilike(user),
            IncentiveVote.chain_id == chain_id,
        )
        .order_by(IncentiveVote.index)
    )

    result = await db.fetch_all(query)

    votes = []
    for row in result:
        vote = UserVote(
            week=row.week,
            receiver_id=row.receiver_id,
            receiver_address=row.receiver_address,
            receiver_label=RECEIVER_MAPPINGS[chain].get(
                row.receiver_id, row.receiver_address
            ),
            points=row.points,
            clearance=row.is_clearance,
            block_number=row.block_number,
            block_timestamp=row.block_timestamp,
            transaction_hash=row.transaction_hash,
        )
        votes.append(vote)

    return UserVoteResponse(votes=votes)


async def get_user_ownership_votes(
    chain_id: int, chain: str, user: str
) -> UserOwnershipVoteResponse:
    Proposal = aliased(OwnershipProposal)

    query = (
        select(
            [
                Proposal.week,
                Proposal.index.label("proposal_index"),
                OwnershipVote.account_weight,
                OwnershipVote.decisive,
                OwnershipVote.block_number,
                OwnershipVote.block_timestamp,
                OwnershipVote.transaction_hash,
            ]
        )
        .join(Proposal, OwnershipVote.proposal_id == Proposal.id)
        .where(
            OwnershipVote.voter_id.ilike(user), Proposal.chain_id == chain_id
        )
        .order_by(OwnershipVote.block_timestamp)
    )

    result = await db.fetch_all(query)

    votes = [
        UserOwnershipVote(
            week=row.week,
            proposal_index=row.proposal_index,
            account_weight=row.account_weight,
            decisive=row.decisive,
            block_number=row.block_number,
            block_timestamp=row.block_timestamp,
            transaction_hash=row.transaction_hash,
        )
        for row in result
    ]

    return UserOwnershipVoteResponse(votes=votes)
