import asyncio
import logging
import sys
import traceback

from database.engine import db, wrap_dbs
from database.models.common import Chain
from database.models.troves import Collateral, StabilityPool, TroveManager
from database.utils import update_by_id_query, upsert_query
from services.celery import celery
from services.sync.collateral import update_price_records
from services.sync.models import ChainData
from services.sync.populate_entities import insert_main_entities
from services.sync.stability_pool import (
    update_pool_operations,
    update_pool_snapshots,
)
from services.sync.trove_manager_snapshots import update_manager_snapshots
from services.sync.trove_snapshots import update_trove_snapshots
from services.sync.update_cues import get_data_for_chain
from utils.const import CHAINS, ethereum

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def back_populate_all():
    for chain, chain_id in CHAINS.items():
        asyncio.run(wrap_dbs(sync_from_subgraph)(chain, chain_id))


@celery.task
def back_populate_chain(chain: str, chain_id: int):
    asyncio.run(wrap_dbs(sync_from_subgraph)(chain, chain_id))


async def _update_stability_pool(
    chain: str, chain_id: int, previous_data: ChainData, new_data: ChainData
):
    if (
        previous_data.stability_pool_data.snapshots_count
        != new_data.stability_pool_data.snapshots_count
    ):
        logger.info(
            f"Detected {new_data.stability_pool_data.snapshots_count - previous_data.stability_pool_data.snapshots_count} changes in stability pool snapshots, syncing"
        )
        try:
            await update_pool_snapshots(
                chain=chain,
                from_index=previous_data.stability_pool_data.snapshots_count,
                to_index=new_data.stability_pool_data.snapshots_count,
            )
        except Exception as e:
            # we need to reset snapshot counts so that next attempts won't skip over the missed data
            logger.error(
                f"Error updating stability pool snaphsots: {e} \n Resetting snapshot count to previous value. \n Old data: {previous_data}\n New data: {new_data}\n{traceback.format_exc()}"
            )
            query = upsert_query(
                StabilityPool,
                {"chain_id": chain_id},
                {
                    "snapshots_count": previous_data.stability_pool_data.snapshots_count
                },
            )
            await db.execute(query)

    if (
        previous_data.stability_pool_data.operations_count
        != new_data.stability_pool_data.operations_count
    ):
        try:
            logger.info(
                f"Detected {new_data.stability_pool_data.operations_count - previous_data.stability_pool_data.operations_count} changes in stability pool operation records, syncing"
            )
            await update_pool_operations(
                chain=chain,
                from_index=previous_data.stability_pool_data.operations_count,
                to_index=new_data.stability_pool_data.operations_count,
            )
        except Exception as e:
            logger.error(
                f"Error updating stability pool operations: {e} \n Resetting operations count to previous value. \n{traceback.format_exc()}"
            )

            query = upsert_query(
                StabilityPool,
                {"chain_id": chain_id},
                {
                    "operations_count": previous_data.stability_pool_data.operations_count
                },
            )
            await db.execute(query)


async def _update_collateral(
    chain: str, previous_data: ChainData, new_data: ChainData
):
    for collateral, collateral_data in new_data.collateral_data.items():
        if (
            collateral not in previous_data.collateral_data
            or collateral_data.latest_price
            != previous_data.collateral_data[collateral].latest_price
        ):
            logger.info(
                f"Detected collateral price change for {collateral}, syncing price records"
            )
            try:
                await update_price_records(
                    chain=chain, collateral_id=collateral
                )
            except Exception as e:
                logger.error(
                    f"Could not update price records, reverting collateral price data: {e}\n{traceback.format_exc()}"
                )
                data = {
                    "latest_price": previous_data.collateral_data[
                        collateral
                    ].latest_price
                    if collateral in previous_data.collateral_data
                    else 0
                }
                query = update_by_id_query(Collateral, collateral, data)
                await db.execute(query)


async def _update_manager(
    chain: str, previous_data: ChainData, new_data: ChainData
):
    for manager, new_manager_data in new_data.trove_manager_data.items():
        if (
            manager not in previous_data.trove_manager_data
            or new_manager_data.snapshots_count
            != previous_data.trove_manager_data[manager].snapshots_count
        ):
            from_index = (
                previous_data.trove_manager_data[manager].snapshots_count
                if manager in previous_data.trove_manager_data
                else 0
            )
            try:
                await update_manager_snapshots(
                    chain=chain,
                    manager_id=manager,
                    from_index=from_index,
                    to_index=new_data.trove_manager_data[
                        manager
                    ].snapshots_count,
                )
            except Exception as e:
                logger.error(
                    f"Error updating manager snapshots: {e}, resetting snapshout count\n{traceback.format_exc()}"
                )
                data = {
                    "snapshots_count": previous_data.trove_manager_data[
                        manager
                    ].snapshots_count
                    if manager in previous_data.trove_manager_data
                    else 0
                }
                query = update_by_id_query(TroveManager, manager, data)
                await db.execute(query)

        if (
            manager not in previous_data.trove_manager_data
            or new_manager_data.trove_snapshots_count
            != previous_data.trove_manager_data[manager].trove_snapshots_count
        ):
            from_index = (
                previous_data.trove_manager_data[manager].trove_snapshots_count
                if manager in previous_data.trove_manager_data
                else 0
            )
            try:
                await update_trove_snapshots(
                    chain=chain,
                    manager_id=manager,
                    from_index=from_index,
                    to_index=new_data.trove_manager_data[
                        manager
                    ].trove_snapshots_count,
                )
            except Exception as e:
                logger.error(
                    f"Error updating trove snapshots: {e}, resetting snapshout count\n{traceback.format_exc()}"
                )
                data = {
                    "trove_snapshots_count": previous_data.trove_manager_data[
                        manager
                    ].trove_snapshots_count
                    if manager in previous_data.trove_manager_data
                    else 0
                }
                query = update_by_id_query(TroveManager, manager, data)
                await db.execute(query)


async def sync_from_subgraph(
    chain: str = ethereum.CHAIN_NAME, chain_id: int = ethereum.CHAIN_ID
):
    await db.execute(upsert_query(Chain, {"id": chain_id}, {"name": chain}))
    previous_data = await get_data_for_chain(chain_id)
    new_data = await insert_main_entities(chain, chain_id)
    if not new_data:
        raise Exception("Failed to retrieve update cues data from the graph")

    await _update_stability_pool(
        chain=chain,
        chain_id=chain_id,
        new_data=new_data,
        previous_data=previous_data,
    )

    await _update_collateral(
        chain=chain, new_data=new_data, previous_data=previous_data
    )

    await _update_manager(
        chain=chain, new_data=new_data, previous_data=previous_data
    )


if __name__ == "__main__":
    back_populate_all()
