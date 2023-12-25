from datetime import timedelta

from utils.const import CHAINS

SUBGRAPH_SYNC_SCHEDULE = {
    f"sync-task-{chain}": {
        "task": "services.sync.back_populate.back_populate_chain",
        "schedule": timedelta(seconds=15),
        "args": (
            chain,
            chain_id,
        ),
    }
    for chain, chain_id in CHAINS.items()
}


PRICE_SYNC_SCHEDULE = {
    f"sync-price-{chain}": {
        "task": "services.prices.populate_mkusd.populate_mkusd_price_history",
        "schedule": timedelta(seconds=3600),
        "args": (
            chain,
            chain_id,
        ),
    }
    for chain, chain_id in CHAINS.items()
}

HOLDERS_SCHEDULE = {
    f"update-holders-{chain}": {
        "task": "services.prices.mkusd_holders.get_holder_data",
        "schedule": timedelta(hours=24),
        "args": (chain,),
    }
    for chain, _ in CHAINS.items()
}

DEPTH_SCHEDULE = {
    f"update-holders-{chain}": {
        "task": "services.prices.liquidity_depth.get_depth_data",
        "schedule": timedelta(minutes=10),
        "args": (chain,),
    }
    for chain, _ in CHAINS.items()
}

IMPACT_SCHEDULE = {
    f"update-impact-{chain}": {
        "task": "services.prices.collateral.get_impact_data",
        "schedule": timedelta(minutes=15),
        "args": (chain,),
    }
    for chain, _ in CHAINS.items()
}

REVENUE_SCHEDULE = {
    f"update-revenue-{chain}": {
        "task": "services.sync.revenue.update_revenue_snapshots",
        "schedule": timedelta(minutes=4),
        "args": (
            chain,
            chain_id,
        ),
    }
    for chain, chain_id in CHAINS.items()
}

CVXPRISMA_SYNC_SCHEDULE = {
    f"sync-cvxprisma-{chain}": {
        "task": "services.cvxprisma.sync.back_populate_cvxprisma",
        "schedule": timedelta(seconds=60),
        "args": (
            chain,
            chain_id,
        ),
    }
    for chain, chain_id in CHAINS.items()
}

DAO_OWNERSHIP_SYNC_SCHEDULE = {
    f"sync-dao-ownership-{chain}": {
        "task": "services.dao.sync.back_populate_ownership_votes",
        "schedule": timedelta(minutes=3),
        "args": (
            chain,
            chain_id,
        ),
    }
    for chain, chain_id in CHAINS.items()
}

DAO_INCENTIVE_SYNC_SCHEDULE = {
    f"sync-dao-incentive-{chain}": {
        "task": "services.dao.sync.back_populate_incentive_votes",
        "schedule": timedelta(minutes=5),
        "args": (
            chain,
            chain_id,
        ),
    }
    for chain, chain_id in CHAINS.items()
}

BOOST_DATA_SCHEDULE = {
    f"sync-dao-incentive-{chain}": {
        "task": "services.dao.sync.back_populate_boost_data",
        "schedule": timedelta(minutes=7),
        "args": (
            chain,
            chain_id,
        ),
    }
    for chain, chain_id in CHAINS.items()
}

CELERY_BEAT_SCHEDULE = {
    # **SUBGRAPH_SYNC_SCHEDULE,
    # **PRICE_SYNC_SCHEDULE,
    # **DEPTH_SCHEDULE,
    # **HOLDERS_SCHEDULE,
    # **IMPACT_SCHEDULE,
    # **CVXPRISMA_SYNC_SCHEDULE,
    # **REVENUE_SCHEDULE,
    # **DAO_OWNERSHIP_SYNC_SCHEDULE,
    # **DAO_INCENTIVE_SYNC_SCHEDULE,
    **BOOST_DATA_SCHEDULE,
}
