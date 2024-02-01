import logging

from database.engine import db
from database.models.troves import (
    Collateral,
    Protocol,
    StabilityPool,
    TroveManager,
)
from database.utils import upsert_query
from services.sync.models import (
    ChainData,
    CollateralData,
    StabilityPoolData,
    TroveManagerData,
)
from utils.const import SUBGRAPHS
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()

ENTITY_QUERY = """
{
  protocols {
    id
    startTime
    priceFeed
    lockersCount
  }

  stabilityPools {
    id
    snapshotsCount
    operationsCount
    totalDeposited
  }

  troveManagers(first: 1000) {
    id
    priceFeed
    sunsetting
    snapshotsCount
    troveSnapshotsCount
    blockNumber
    blockTimestamp
    transactionHash
    collateral {
      id
      name
      decimals
      symbol
      latestPrice
    }
  }

}
"""


async def insert_main_entities(chain: str, chain_id: int) -> ChainData | None:
    endpoint = SUBGRAPHS[chain]
    entity_data = await async_grt_query(endpoint=endpoint, query=ENTITY_QUERY)
    if not entity_data:
        logger.error(
            f"Did not receive any data from the graph on chain {chain} when querying for base entities"
        )
        return None
    # Create main protocol entity
    protocol = entity_data["protocols"][0]
    indexes = {"chain_id": chain_id}
    data = {
        "start_time": protocol["startTime"],
        "price_feed": protocol["priceFeed"],
        "lockers_count": protocol["lockersCount"],
    }
    query = upsert_query(Protocol, indexes, data)
    await db.execute(query)

    # Create stability pool
    pool = entity_data["stabilityPools"][0]
    indexes = {"chain_id": chain_id, "address": pool["id"]}
    data = {
        "snapshots_count": pool["snapshotsCount"],
        "operations_count": pool["operationsCount"],
        "total_deposited": pool["totalDeposited"],
    }
    query = upsert_query(
        StabilityPool, indexes, data, return_columns=[StabilityPool.id]
    )
    pool_id = await db.execute(query)
    if not pool_id:
        raise Exception(
            f"Could not create entry for stability pool ID: {pool['id']}"
        )
    pool_data = StabilityPoolData(
        snapshots_count=pool["snapshotsCount"],
        operations_count=pool["operationsCount"],
    )

    # Create trove managers
    manager_data: dict[int, TroveManagerData] = {}
    collateral_data: dict[int, CollateralData] = {}
    for manager in entity_data["troveManagers"]:

        # Create collateral for the manager
        collateral = manager["collateral"]
        indexes = {"chain_id": chain_id, "address": collateral["id"]}
        data = {
            "name": collateral["name"],
            "decimals": collateral["decimals"],
            "symbol": collateral["symbol"],
            "latest_price": collateral["latestPrice"],
            "stability_pool_id": pool_id,
        }
        query = upsert_query(
            Collateral, indexes, data, return_columns=[Collateral.id]
        )
        collateral_id = await db.execute(query)
        if not collateral_id:
            raise Exception(
                f"Could not create entry for collateral ID: {manager['id']}"
            )

        # Create the manager entry
        indexes = {"chain_id": chain_id, "address": manager["id"]}
        data = {
            "price_feed": manager["priceFeed"],
            "sunsetting": manager["sunsetting"],
            "trove_snapshots_count": manager["troveSnapshotsCount"],
            "collateral_id": collateral_id,
            "snapshots_count": manager["snapshotsCount"],
            "block_number": manager["blockNumber"],
            "block_timestamp": manager["blockTimestamp"],
            "transaction_hash": manager["transactionHash"],
        }
        query = upsert_query(
            TroveManager, indexes, data, return_columns=[TroveManager.id]
        )
        manager_id = await db.execute(query)
        if not manager_id:
            raise Exception(
                f"Could not create entry for trove manager ID: {manager['id']}"
            )
        manager_data[manager_id] = TroveManagerData(
            trove_snapshots_count=manager["troveSnapshotsCount"],
            snapshots_count=manager["snapshotsCount"],
        )
        collateral_data[collateral_id] = CollateralData(
            latest_price=float(collateral["latestPrice"])
        )

    return ChainData(
        trove_manager_data=manager_data,
        collateral_data=collateral_data,
        stability_pool_data=pool_data,
    )
