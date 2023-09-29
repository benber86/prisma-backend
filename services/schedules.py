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

CELERY_BEAT_SCHEDULE = {**SUBGRAPH_SYNC_SCHEDULE, **PRICE_SYNC_SCHEDULE}
