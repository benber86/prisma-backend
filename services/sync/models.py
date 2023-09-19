from pydantic import BaseModel


class TroveManagerData(BaseModel):
    trove_snapshots_count: int
    snapshots_count: int


class CollateralData(BaseModel):
    latest_price: float


class StabilityPoolData(BaseModel):
    snapshots_count: int
    operations_count: int


class ChainData(BaseModel):
    trove_manager_data: dict[int, TroveManagerData]
    collateral_data: dict[int, CollateralData]
    stability_pool_data: StabilityPoolData
