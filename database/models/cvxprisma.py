from enum import Enum

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database.base import Base
from database.models.common import Chain


class CvxPrismaStaking(Base):
    __tablename__ = "cvx_prisma_staking"

    id = Column(String, primary_key=True)
    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    token_balance = Column(Numeric)
    tvl = Column(Numeric)
    deposit_count = Column(Numeric)
    withdraw_count = Column(Numeric)
    payout_count = Column(Numeric)
    snapshot_count = Column(Numeric)
    __table_args__ = (
        Index(
            "idx_cvx_prisma_staking__chain_id__id",
            chain_id,
            id,
            unique=True,
        ),
    )


class StakeEvent(Base):
    __tablename__ = "stake_event"

    class StakeOperation(Enum):
        withdraw = "withdraw"
        stake = "stake"

    staking_id = Column(ForeignKey("cvx_prisma_staking.id"))
    user_id = Column(ForeignKey("users.id"))
    operation = Column(sa.Enum(StakeOperation))
    amount = Column(Numeric)
    amount_usd = Column(Numeric)
    index = Column(Integer)

    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    staking = relationship("CvxPrismaStaking")
    user = relationship("User")

    __table_args__ = (
        Index(
            "idx_stake_event__staking_id__user_id__index",
            staking_id,
            user_id,
            index,
            unique=True,
        ),
    )


class RewardPaid(Base):
    __tablename__ = "reward_paid"
    staking_id = Column(ForeignKey("cvx_prisma_staking.id"))
    user_id = Column(ForeignKey("users.id"))

    token_address = Column(String)
    token_symbol = Column(String)
    amount = Column(Numeric)
    amount_usd = Column(Numeric)
    index = Column(Integer)

    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    staking = relationship("CvxPrismaStaking")
    user = relationship("User")

    __table_args__ = (
        Index(
            "idx_reward_paid__staking_id__user_id__index",
            staking_id,
            user_id,
            index,
            unique=True,
        ),
    )


class StakingBalance(Base):
    __tablename__ = "staking_balance"
    staking_id = Column(ForeignKey("cvx_prisma_staking.id"))
    user_id = Column(ForeignKey("users.id"))
    stake_size = Column(Numeric)
    timestamp = Column(Numeric)

    staking = relationship("CvxPrismaStaking")
    user = relationship("User")

    __table_args__ = (
        Index(
            "idx_staking_balance__staking_id__user_id__timestamp",
            staking_id,
            user_id,
            timestamp,
            unique=True,
        ),
    )


class StakingSnapshot(Base):
    __tablename__ = "staking_snapshot"
    staking_id = Column(ForeignKey("cvx_prisma_staking.id"))

    token_balance = Column(Numeric)
    token_supply = Column(Numeric)
    tvl = Column(Numeric)
    total_apr = Column(Numeric)
    apr_breakdown = Column(JSONB)
    timestamp = Column(Numeric)

    staking = relationship("CvxPrismaStaking")
    __table_args__ = (
        Index(
            "idx_staking_snapshot__staking_id__timestamp",
            staking_id,
            timestamp,
            unique=True,
        ),
    )
