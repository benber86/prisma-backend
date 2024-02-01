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
from sqlalchemy.orm import relationship

from database.base import Base
from database.models.common import Chain


class Protocol(Base):
    __tablename__ = "protocols"

    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    start_time = Column(Numeric)
    price_feed = Column(String)
    lockers_count = Column(Integer)
    chain = relationship("Chain", backref="protocols")

    __table_args__ = (
        Index(
            "idx_protocols__chain_id",
            chain_id,
            unique=True,
        ),
    )


class Collateral(Base):
    __tablename__ = "collaterals"

    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    address = Column(String)
    name = Column(String)
    decimals = Column(Integer)
    symbol = Column(String)
    latest_price = Column(Numeric)
    managers = relationship("TroveManager", back_populates="collateral")
    chain = relationship("Chain")
    stability_pool_id = Column(ForeignKey("stability_pool.id"))
    stability_pool = relationship(
        "StabilityPool", back_populates="collaterals"
    )

    __table_args__ = (
        Index(
            "idx_collaterals__chain_id__address",
            chain_id,
            address,
            unique=True,
        ),
    )


class TroveManagerParameter(Base):
    __tablename__ = "trove_manager_parameters"

    id = Column(String, primary_key=True)
    minute_decay_factor = Column(Numeric)
    redemption_fee_floor = Column(Numeric)
    max_redemption_fee = Column(Numeric)
    borrowing_fee_floor = Column(Numeric)
    max_borrowing_fee = Column(Numeric)
    max_system_debt = Column(Numeric)
    interest_rate = Column(Numeric)
    mcr = Column(Numeric)
    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)
    manager_id = Column(ForeignKey("trove_managers.id"))

    manager = relationship("TroveManager")

    __table_args__ = (
        Index(
            "idx_trove_manager_parameters__manager_id__block_timestamp",
            manager_id,
            block_timestamp,
            unique=True,
        ),
    )


class TroveManager(Base):
    __tablename__ = "trove_managers"

    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    address = Column(String)
    price_feed = Column(String)
    sunsetting = Column(Boolean)
    snapshots_count = Column(Integer)
    trove_snapshots_count = Column(Integer)
    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    collateral_id = Column(ForeignKey("collaterals.id"))
    collateral = relationship("Collateral", back_populates="managers")
    chain = relationship("Chain")
    troves = relationship("Trove", back_populates="manager")
    snapshots = relationship("TroveManagerSnapshot", back_populates="manager")

    __table_args__ = (
        Index(
            "idx_trove_managers__chain_id__address",
            chain_id,
            address,
            unique=True,
        ),
    )


class TroveManagerSnapshot(Base):
    __tablename__ = "trove_manager_snapshots"

    manager_id = Column(ForeignKey("trove_managers.id"))
    index = Column(Integer)
    collateral_price = Column(Numeric)
    rate = Column(Numeric)
    borrowing_fee = Column(Numeric)
    collateral_ratio = Column(Numeric)
    total_collateral = Column(Numeric)
    total_collateral_usd = Column(Numeric)
    total_debt = Column(Numeric)
    total_stakes = Column(Numeric)
    total_borrowing_fees_paid = Column(Numeric)
    total_redemption_fees_paid = Column(Numeric)
    total_redemption_fees_paid_usd = Column(Numeric)
    total_collateral_redistributed = Column(Numeric)
    total_collateral_redistributed_usd = Column(Numeric)
    total_debt_redistributed = Column(Numeric)
    open_troves = Column(Integer)
    total_troves_opened = Column(Integer)
    liquidated_troves = Column(Integer)
    total_troves_liquidated = Column(Integer)
    redeemed_troves = Column(Integer)
    total_troves_redeemed = Column(Integer)
    closed_troves = Column(Integer)
    total_troves_closed = Column(Integer)
    total_troves = Column(Integer)
    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)
    parameters_id = Column(ForeignKey("trove_manager_parameters.id"))

    manager = relationship("TroveManager", back_populates="snapshots")
    parameters = relationship("TroveManagerParameter")

    __table_args__ = (
        Index(
            "idx_trove_manager_snapshots__manager_id__block_timestamp__index",
            manager_id,
            block_timestamp,
            index,
            unique=True,
        ),
    )


class Trove(Base):
    __tablename__ = "troves"

    class TroveStatus(Enum):
        open = "open"
        closed_by_owner = "closedByOwner"
        closed_by_liquidation = "closedByLiquidation"
        closed_by_redemption = "closedByRedemption"

    owner_id = Column(ForeignKey("users.id"))
    status = Column(sa.Enum(TroveStatus))
    manager_id = Column(ForeignKey("trove_managers.id"))
    snapshots_count = Column(Integer)
    collateral = Column(Numeric)
    collateral_usd = Column(Numeric)
    debt = Column(Numeric)
    stake = Column(Numeric)
    reward_snapshot_collateral = Column(Numeric)
    reward_snapshot_debt = Column(Numeric)

    owner = relationship("User")
    manager = relationship("TroveManager", back_populates="troves")
    snapshots = relationship("TroveSnapshot", back_populates="trove")

    __table_args__ = (
        Index(
            "idx_troves__manager_id__owner_id",
            manager_id,
            owner_id,
            unique=True,
        ),
    )


class TroveSnapshot(Base):
    __tablename__ = "trove_snapshots"

    class TroveOperation(Enum):
        open_trove = "openTrove"
        close_trove = "closeTrove"
        adjust_trove = "adjustTrove"
        apply_pending_rewards = "applyPendingRewards"
        liquidate_in_normal_mode = "liquidateInNormalMode"
        liquidate_in_recovery_mode = "liquidateInRecoveryMode"
        redeem_collateral = "redeemCollateral"

    trove_id = Column(ForeignKey("troves.id"))
    operation = Column(sa.Enum(TroveOperation))
    index = Column(Integer)
    collateral = Column(Numeric)
    collateral_usd = Column(Numeric)
    collateral_ratio = Column(Numeric)
    debt = Column(Numeric)
    stake = Column(Numeric)
    borrowing_fee = Column(Numeric)
    liquidation_id = Column(ForeignKey("liquidations.id"))
    redemption_id = Column(ForeignKey("redemptions.id"))
    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    trove = relationship("Trove", back_populates="snapshots")
    liquidation = relationship("Liquidation", back_populates="troves_affected")
    redemption = relationship("Redemption", back_populates="troves_affected")

    __table_args__ = (
        Index(
            "idx_trove_snapshots__trove_id__block_timestamp__index",
            trove_id,
            block_timestamp,
            index,
            unique=True,
        ),
    )


class StabilityPool(Base):
    __tablename__ = "stability_pool"

    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    address = Column(String)
    snapshots_count = Column(Integer)
    operations_count = Column(Integer)
    total_deposited = Column(Numeric)
    chain = relationship("Chain")
    collaterals = relationship("Collateral", back_populates="stability_pool")

    __table_args__ = (
        Index(
            "idx_stability_pool__chain_id__address",
            chain_id,
            address,
            unique=True,
        ),
    )


class StabilityPoolSnapshot(Base):
    __tablename__ = "stability_pool_snapshots"

    index = Column(Integer)
    pool_id = Column(ForeignKey("stability_pool.id"))
    total_deposited = Column(Numeric)
    total_collateral_withdrawn_usd = Column(Numeric)
    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    pool = relationship("StabilityPool")

    __table_args__ = (
        Index(
            "idx_stability_pool_snapshots__pool_id__index__block_timestamp",
            pool_id,
            index,
            block_timestamp,
            unique=True,
        ),
    )


class StabilityPoolOperation(Base):
    __tablename__ = "sp_ops"

    class StabilityPoolOperationType(Enum):
        stable_deposit = "stableDeposit"
        stable_withdrawal = "stableWithdrawal"
        collateral_withdrawal = "collateralWithdrawal"

    user_id = Column(String, ForeignKey("users.id"))
    pool_id = Column(ForeignKey("stability_pool.id"))
    operation = Column(sa.Enum(StabilityPoolOperationType))
    index = Column(Integer)
    stable_amount = Column(Numeric)
    user_deposit = Column(Numeric)
    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    withdrawn_collaterals = relationship(
        "CollateralWithdrawal", back_populates="operation"
    )
    user = relationship("User", back_populates="stabilityPoolOperations")
    pool = relationship("StabilityPool")

    __table_args__ = (
        Index(
            "idx_sp_ops__pool_id__user_id__index__block_timestamp",
            pool_id,
            user_id,
            index,
            block_timestamp,
            unique=True,
        ),
    )


class CollateralWithdrawal(Base):
    __tablename__ = "collateral_withdrawals"

    collateral_id = Column(ForeignKey("collaterals.id"))
    collateral_amount = Column(Numeric)
    collateral_amount_usd = Column(Numeric)
    operation_id = Column(ForeignKey("sp_ops.id"))
    operation = relationship(
        "StabilityPoolOperation", back_populates="withdrawn_collaterals"
    )
    collateral = relationship("Collateral")

    __table_args__ = (
        Index(
            "idx_collateral_withdrawals__collateral_id__operation_id",
            collateral_id,
            operation_id,
            unique=True,
        ),
    )


class Liquidation(Base):
    __tablename__ = "liquidations"

    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    liquidator_id = Column(ForeignKey("users.id"))
    liquidated_debt = Column(Numeric)
    liquidated_collateral = Column(Numeric)
    liquidated_collateral_usd = Column(Numeric)
    coll_gas_compensation = Column(Numeric)
    coll_gas_compensation_usd = Column(Numeric)
    debt_gas_compensation = Column(Numeric)
    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    troves_affected = relationship(
        "TroveSnapshot", back_populates="liquidation"
    )
    chain = relationship("Chain")
    liquidator = relationship("User")

    __table_args__ = (
        Index(
            "idx_liquidations__chain_id__liquidator_id__block_timestamp",
            chain_id,
            liquidator_id,
            block_timestamp,
            unique=True,
        ),
    )


class Redemption(Base):
    __tablename__ = "redemptions"

    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    redeemer_id = Column(ForeignKey("users.id"))
    attempted_debt_amount = Column(Numeric)
    actual_debt_amount = Column(Numeric)
    collateral_sent = Column(Numeric)
    collateral_sent_usd = Column(Numeric)
    collateral_sent_to_redeemer = Column(Numeric)
    collateral_sent_to_redeemer_usd = Column(Numeric)
    collateral_fee = Column(Numeric)
    collateral_fee_usd = Column(Numeric)
    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    troves_affected = relationship(
        "TroveSnapshot", back_populates="redemption"
    )
    chain = relationship("Chain")
    redeemer = relationship("User")

    __table_args__ = (
        Index(
            "idx_redemptions__chain_id__redeemer_id__block_timestamp",
            chain_id,
            redeemer_id,
            block_timestamp,
            unique=True,
        ),
    )


class PriceRecord(Base):
    __tablename__ = "price_records"

    collateral_id = Column(ForeignKey("collaterals.id"))
    price = Column(Numeric)
    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    collateral = relationship("Collateral")

    __table_args__ = (
        Index(
            "idx_price_records__collateral_id__block_timestamp",
            collateral_id,
            block_timestamp,
            unique=True,
        ),
    )


class ZapStakes(Base):
    __tablename__ = "zap_stakes"

    collateral_id = Column(ForeignKey("collaterals.id"))
    amount = Column(Numeric)
    index = Column(Integer)
    block_number = Column(Numeric)
    block_timestamp = Column(Numeric)
    transaction_hash = Column(String)

    collateral = relationship("Collateral")

    __table_args__ = (
        Index(
            "idx_zap_stakes__collateral_id__index__block_timestamp",
            collateral_id,
            index,
            block_timestamp,
            unique=True,
        ),
    )
