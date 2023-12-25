import logging
from enum import Enum

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import aliased
from web3 import Web3

from api.models.common import DecimalTimeSeries, Pagination
from api.routes.v1.rest.dao.models import (
    AvailableAtFee,
    AvailableAtFeeResponse,
    DelegationUser,
    DelegationUserResponse,
    OrderFilter,
    OwnershipProposalDetail,
    OwnershipProposalDetailResponse,
    UserOwnershipVote,
    UserOwnershipVoteResponse,
    UserVote,
    UserVoteResponse,
    WeeklyBoostUsage,
    WeeklyClaimData,
    WeeklyClaimDataResponse,
    WeeklyUserVote,
    WeeklyUserVoteData,
    WeeklyUserVoteDataResponse,
)
from database.engine import db
from database.models.common import User
from database.models.dao import (
    BatchRewardClaim,
    IncentiveReceiver,
    IncentiveVote,
    OwnershipProposal,
    OwnershipVote,
    UserWeeklyIncentivePoints,
    WeeklyBoostData,
)
from utils.const import RECEIVER_MAPPINGS
from utils.time import get_week


async def search_ownership_proposals(
    chain_id: int,
    pagination: Pagination,
    order: OrderFilter,
) -> OwnershipProposalDetailResponse:

    base_query = (
        select([OwnershipProposal, User.label.label("creator_label")])
        .join(User, OwnershipProposal.creator_id == User.id)
        .where(OwnershipProposal.chain_id == chain_id)
    )

    if order.creator_filter:
        base_query = base_query.where(
            OwnershipProposal.creator_id == order.creator_filter
        )
    if order.decode_data_filter:
        base_query = base_query.where(
            OwnershipProposal.decode_data == order.decode_data_filter
        )

    count_query = select([func.count()]).select_from(
        base_query.alias("subquery")
    )
    total_count = await db.fetch_val(count_query)

    order_column = getattr(OwnershipProposal, order.order_by)  # type: ignore
    if order.desc:
        base_query = base_query.order_by(order_column.desc())
    else:
        base_query = base_query.order_by(order_column)

    items_per_page = pagination.items
    offset = (pagination.page - 1) * items_per_page
    query_with_pagination = base_query.limit(items_per_page).offset(offset)

    results = await db.fetch_all(query_with_pagination)

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

    return OwnershipProposalDetailResponse(
        proposals=proposals, count=total_count
    )


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


async def get_boost_breakdown(
    chain_id: int, user: str
) -> WeeklyClaimDataResponse:
    query = (
        select(
            [
                WeeklyBoostData.week,
                func.sum(WeeklyBoostData.eligible_for).label("eligible"),
                func.sum(WeeklyBoostData.self_claimed).label("self_claimed"),
                func.sum(WeeklyBoostData.other_claimed).label(
                    "delegate_claimed"
                ),
            ]
        )
        .where(
            WeeklyBoostData.chain_id == chain_id,
            WeeklyBoostData.user_id.ilike(user),
        )
        .group_by(WeeklyBoostData.week)
    )

    results = await db.fetch_all(query)

    claims = [
        WeeklyClaimData(
            week=result.week,
            eligible=float(result.eligible),
            self_claimed=float(result.self_claimed),
            delegate_claimed=float(result.delegate_claimed),
            left_over=max(
                0.0,
                float(result.eligible)
                - float(result.self_claimed)
                - float(result.delegate_claimed),
            ),
        )
        for result in results
    ]

    return WeeklyClaimDataResponse(claims=claims)


async def get_weekly_boost_use(
    chain_id: int, week: int, delegate: str
) -> WeeklyBoostUsage:
    query = (
        select(
            [
                BatchRewardClaim.delegate_remaining_eligible,
                BatchRewardClaim.block_timestamp,
            ]
        )
        .where(
            BatchRewardClaim.chain_id == chain_id,
            BatchRewardClaim.week == week,
            BatchRewardClaim.delegate_id.ilike(delegate),
        )
        .order_by(BatchRewardClaim.block_timestamp)
    )

    results = await db.fetch_all(query)

    boost_usage_data = [
        DecimalTimeSeries(
            value=float(result.delegate_remaining_eligible),
            timestamp=int(result.block_timestamp),
        )
        for result in results
    ]

    return WeeklyBoostUsage(boost=boost_usage_data)


async def get_historical_fee_accrued(
    chain_id: int, delegate: str
) -> list[DecimalTimeSeries]:
    query = (
        select(
            [BatchRewardClaim.block_timestamp, BatchRewardClaim.fee_generated]
        )
        .where(
            BatchRewardClaim.chain_id == chain_id,
            BatchRewardClaim.fee_generated > 0,
            BatchRewardClaim.delegate_id.ilike(delegate),
        )
        .order_by(BatchRewardClaim.block_timestamp)
    )

    results = await db.fetch_all(query)

    cumulative_sum = 0.0
    cumulative_fees = []
    for result in results:
        cumulative_sum += float(result.fee_generated)
        cumulative_fees.append(
            DecimalTimeSeries(
                value=cumulative_sum, timestamp=int(result.block_timestamp)
            )
        )

    return cumulative_fees


async def get_delegation_users(
    chain_id: int, delegate: str
) -> DelegationUserResponse:
    query = (
        select(
            [
                User.id.label("address"),
                User.label,
                func.sum(BatchRewardClaim.fee_generated).label("fees"),
                func.count(BatchRewardClaim.id).label("claim_count"),
            ]
        )
        .join(User, BatchRewardClaim.caller_id == User.id)
        .where(
            BatchRewardClaim.chain_id == chain_id,
            BatchRewardClaim.delegate_id.ilike(delegate),
        )
        .group_by(User.id, User.label)
        .order_by(func.sum(BatchRewardClaim.fee_generated).desc())
    )

    results = await db.fetch_all(query)

    delegation_users = [
        DelegationUser(
            address=result.address,
            label=result.label,
            fees=float(result.fees),
            count=result.claim_count,
        )
        for result in results
    ]
    return DelegationUserResponse(users=delegation_users)


async def get_top_delegation_users(
    chain_id: int, top: int, week: int
) -> DelegationUserResponse:
    query = (
        select(
            [
                User.id.label("address"),
                User.label,
                WeeklyBoostData.accrued_fees.label("fees"),
                WeeklyBoostData.boost_delegation_users.label("user_count"),
            ]
        )
        .join(User, WeeklyBoostData.user_id == User.id)
        .where(
            WeeklyBoostData.chain_id == chain_id, WeeklyBoostData.week == week
        )
        .order_by(WeeklyBoostData.accrued_fees.desc())
        .limit(top)
    )

    results = await db.fetch_all(query)

    delegation_users = [
        DelegationUser(
            address=result.address,
            label=result.label,
            fees=float(result.fees),
            count=result.user_count,
        )
        for result in results
    ]

    return DelegationUserResponse(users=delegation_users)


async def get_emissions_data(
    chain_id: int, week: int
) -> AvailableAtFeeResponse:
    query = (
        select(
            [
                func.coalesce(
                    WeeklyBoostData.non_locking_fee,
                    WeeklyBoostData.last_applied_fee,
                ).label("fee"),
                func.greatest(
                    0,
                    (
                        WeeklyBoostData.eligible_for
                        - WeeklyBoostData.total_claimed
                    ),
                ).label("available_emissions"),
            ]
        )
        .where(
            WeeklyBoostData.chain_id == chain_id,
            WeeklyBoostData.week == week,
            or_(
                WeeklyBoostData.non_locking_fee < 100,
                and_(
                    WeeklyBoostData.non_locking_fee.is_(None),
                    WeeklyBoostData.last_applied_fee < 100,
                ),
            ),
        )
        .order_by("fee")
    )

    results = await db.fetch_all(query)

    cumulative_emissions = 0.0
    emissions_data = []
    for result in results:
        cumulative_emissions += float(result.available_emissions)
        emissions_data.append(
            AvailableAtFee(
                available=cumulative_emissions, fee=float(result.fee)
            )
        )

    return AvailableAtFeeResponse(emissions=emissions_data)
