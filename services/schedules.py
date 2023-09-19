from datetime import timedelta

from utils.const import CHAINS

CELERY_BEAT_SCHEDULE = {
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
