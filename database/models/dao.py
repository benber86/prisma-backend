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

    id = Column(String, primary_key=True)
    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    creator_id = Column(ForeignKey("users.id"))
    creator = relationship("User")
    status = Column(sa.Enum(OwnershipProposalStatus))
    index = Column(Integer)
    target = Column(String)
    data = Column(String)
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
            "idx_ownership_proposals__chain_id__id",
            chain_id,
            id,
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
            "idx_ownership_vote__proposal_id__user_id",
            proposal_id,
            voter_id,
            index,
            unique=True,
        ),
    )


class IncentiveReceiver(Base):
    __tablename__ = "incentive_receivers"
    id = Column(String, primary_key=True)
    address = Column(String)
    is_active = Column(Boolean)

    __table_args__ = (
        Index(
            "idx_incentive_receivers__address",
            address,
            unique=True,
        ),
    )


class IncentiveVote(Base):
    __tablename__ = "incentive_votes"
    voter_id = Column(ForeignKey("users.id"))
    index = Column(Integer)
    week = Column(Integer)
    weight = Column(Integer)
    is_clearance = Column(Boolean)
    target_id = Column(ForeignKey("incentive_receivers.id"))

    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    voter = relationship("User")
    target = relationship("IncentiveReceiver")

    __table_args__ = (
        Index(
            "idx_incentive_votes__voter_id__target_id",
            voter_id,
            target_id,
            unique=True,
        ),
    )
