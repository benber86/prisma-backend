from sqlalchemy import (
    BigInteger,
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


class Chain(Base):
    __tablename__ = "chains"
    id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    total_deposited = Column(Numeric)
    total_collateral_gained_usd = Column(Numeric)
    vote_count = Column(Integer)
    lock_balance = Column(Numeric)
    frozen = Column(Boolean)
    label = Column(String)
    stabilityPoolOperations = relationship(
        "StabilityPoolOperation", back_populates="user"
    )


class StableCoinPrice(Base):
    __tablename__ = "mkusd_price"
    chain_id = Column(ForeignKey("chains.id"), nullable=False)
    price = Column(Numeric)
    timestamp = Column(Integer)
    chain = relationship("Chain")

    __table_args__ = (
        Index(
            "idx_collaterals__chain_id__timestamp",
            chain_id,
            timestamp,
            unique=True,
        ),
    )
