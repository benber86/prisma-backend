import asyncio
import logging
from datetime import datetime, timezone

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


def _parse_timestamp(date: str) -> int:
    dt = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
    return int(dt.replace(tzinfo=timezone.utc).timestamp())


def _get_price_info_from_curve_prices(chain: str) -> list[LlammaPriceSeries]:
    current_timestamp = int(datetime.utcnow().timestamp())
    start_timestamp = current_timestamp - (60 * 60 * 24 * 7)
    address = STABLECOINS[chain]
    cp_endpoint = f"https://prices.curve.fi/v1/usd_price/{chain}/{address}/history?interval=hour&start={start_timestamp}&end={current_timestamp}"
    r = requests.get(cp_endpoint)
    return [
        LlammaPriceSeries(
            price=data["price"], timestamp=_parse_timestamp(data["timestamp"])
        )
        for data in r.json()["data"]
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
    data = _get_price_info_from_curve_prices(chain)
    await _update_db_with_llama_prices(chain_id, data)


@celery.task
def populate_mkusd_price_history(chain: str, chain_id: int):
    asyncio.run(wrap_dbs(update_mkusd_price_history)(chain, chain_id))
