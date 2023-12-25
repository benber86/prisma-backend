from enum import Enum

import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database.base import Base
from database.models.common import Chain


class OwnershipProposal(Base):
    __tablename__ = "ownership_proposals"

    class OwnershipProposalStatus(Enum):
        not_passed = "not_passed"
        passed = "passed"
        cancelled = "cancelled"
        executed = "executed"

    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    creator_id = Column(ForeignKey("users.id"))
    creator = relationship("User")
    status = Column(sa.Enum(OwnershipProposalStatus))
    index = Column(Integer)
    data = Column(JSONB)
    decode_data = Column(String)
    week = Column(Integer)
    required_weight = Column(Numeric)
    received_weight = Column(Numeric)
    can_execute_after = Column(Integer)
    vote_count = Column(Integer)
    execution_tx = Column(String)

    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    __table_args__ = (
        Index(
            "idx_ownership_proposals__chain_id__creator_id__index",
            chain_id,
            creator_id,
            index,
            unique=True,
        ),
    )


class OwnershipVote(Base):
    __tablename__ = "ownership_vote"

    proposal_id = Column(ForeignKey("ownership_proposals.id"))
    voter_id = Column(ForeignKey("users.id"))
    weight = Column(Numeric)
    index = Column(Integer)
    account_weight = Column(Numeric)
    decisive = Column(Boolean)

    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    proposal = relationship("OwnershipProposal")
    voter = relationship("User")

    __table_args__ = (
        Index(
            "idx_ownership_vote__proposal_id__user_id__index",
            proposal_id,
            voter_id,
            index,
            unique=True,
        ),
    )


class IncentiveReceiver(Base):
    __tablename__ = "incentive_receivers"
    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    index = Column(Integer)
    address = Column(String)
    is_active = Column(Boolean)

    __table_args__ = (
        Index(
            "idx_incentive_receivers__address__index__chain_id",
            address,
            index,
            chain_id,
            unique=True,
        ),
    )


class IncentiveVote(Base):
    __tablename__ = "incentive_votes"
    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    voter_id = Column(ForeignKey("users.id"))
    index = Column(Integer)
    week = Column(Integer)
    points = Column(Integer)
    is_clearance = Column(Boolean)
    target_id = Column(ForeignKey("incentive_receivers.id"))

    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    voter = relationship("User")
    target = relationship("IncentiveReceiver")

    __table_args__ = (
        Index(
            "idx_incentive_votes__index__week__chain_id__voter_id__target_id",
            index,
            week,
            chain_id,
            voter_id,
            target_id,
            unique=True,
        ),
    )


class UserWeeklyIncentivePoints(Base):
    __tablename__ = "user_incent_points"
    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    voter_id = Column(ForeignKey("users.id"))
    receiver_id = Column(ForeignKey("incentive_receivers.id"))

    week = Column(Integer)
    points = Column(Integer)

    voter = relationship("User")
    receiver = relationship("IncentiveReceiver")

    __table_args__ = (
        Index(
            "idx_user_incent_points__week__chain_id__voter_id__receiver_id",
            week,
            chain_id,
            voter_id,
            receiver_id,
            unique=True,
        ),
    )


class WeeklyBoostData(Base):
    __tablename__ = "weekly_boost"
    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    user_id = Column(ForeignKey("users.id"))
    week = Column(Integer)
    boost = Column(Numeric)
    pct = Column(Numeric)
    last_applied_fee = Column(Numeric)
    non_locking_fee = Column(Numeric)
    boost_delegation = Column(Boolean)
    boost_delegation_users = Column(Numeric)
    eligible_for = Column(Numeric)
    total_claimed = Column(Numeric)
    self_claimed = Column(Numeric)
    other_claimed = Column(Numeric)
    accrued_fees = Column(Numeric)
    time_to_depletion = Column(Numeric)

    user = relationship("User")

    __table_args__ = (
        Index(
            "idx_weekly_boost__week__chain_id__user_id",
            week,
            chain_id,
            user_id,
            unique=True,
        ),
    )


class BatchRewardClaim(Base):
    __tablename__ = "batch_claims"
    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    caller_id = Column(ForeignKey("users.id"))
    receiver_id = Column(ForeignKey("users.id"))
    delegate_id = Column(ForeignKey("users.id"))
    week = Column(Integer)
    index = Column(Integer)
    total_claimed = Column(Numeric)
    total_claimed_boosted = Column(Numeric)
    delegate_remaining_eligible = Column(Numeric)
    max_fee = Column(Numeric)
    fee_generated = Column(Numeric)
    fee_applied = Column(Numeric)

    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    caller = relationship("User", foreign_keys=[caller_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
    delegate = relationship("User", foreign_keys=[delegate_id])

    __table_args__ = (
        Index(
            "idx_batch_claims__week__chain_id__caller_id__delegate_id__index",
            week,
            chain_id,
            caller_id,
            delegate_id,
            index,
            unique=True,
        ),
    )


class WeeklyEmissions(Base):
    __tablename__ = "weekly_emissions"
    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    week = Column(Integer)
    emissions = Column(Numeric)

    __table_args__ = (
        Index(
            "idx_weekly_emissions__week__chain_id",
            week,
            chain_id,
            unique=True,
        ),
    )
