import asyncio
import logging
from datetime import datetime

import requests
from pydantic import BaseModel

from database.engine import db, wrap_dbs
from database.models.common import StableCoinPrice
from database.utils import upsert_query
from services.celery import celery
from utils.const import STABLECOINS
from utils.const.chains import ethereum

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LlammaPriceSeries(BaseModel):
    price: float
    timestamp: int


def _get_price_info_from_defi_llamma(chain: str) -> list[LlammaPriceSeries]:
    current_timestamp = datetime.utcnow().timestamp()
    address = STABLECOINS[chain]
    dl_endpoint = f"https://coins.llama.fi/chart/{chain}:{address}?end={current_timestamp}&span=1000&period=1h"
    r = requests.get(dl_endpoint)
    return [
        LlammaPriceSeries(**data)
        for data in r.json()["coins"][f"{chain}:{address}"]["prices"]
    ]


async def _update_db_with_llama_prices(
    chain_id: int, data: list[LlammaPriceSeries]
):
    for price in data:
        indexes = {
            "chain_id": chain_id,
            "timestamp": price.timestamp,
        }
        query = upsert_query(StableCoinPrice, indexes, {"price": price.price})
        await db.execute(query)


async def update_mkusd_price_history(
    chain: str = ethereum.CHAIN_NAME, chain_id: int = ethereum.CHAIN_ID
):
    data = _get_price_info_from_defi_llamma(chain)
    await _update_db_with_llama_prices(chain_id, data)


@celery.task
def populate_mkusd_price_history(chain: str, chain_id: int):
    asyncio.run(wrap_dbs(update_mkusd_price_history)(chain, chain_id))
