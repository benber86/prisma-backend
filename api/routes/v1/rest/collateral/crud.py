import logging
from datetime import datetime
from operator import and_

import aiohttp
from aiocache import Cache, cached
from sqlalchemy import select

from api.models.common import DecimalTimeSeries, Period
from api.routes.utils.time import apply_period
from database.engine import db
from database.models.troves import PriceRecord
from utils.const import CBETH, RETH, SFRXETH, WSTETH

logger = logging.getLogger()


@cached(ttl=300, cache=Cache.MEMORY)
async def get_market_prices(
    chain: str, collateral: str, period: Period
) -> list[DecimalTimeSeries]:
    collat = collateral.lower()
    current_timestamp = datetime.utcnow().timestamp()
    start_timestamp = apply_period(period)
    span = int((current_timestamp - start_timestamp) // (4 * 3600))
    url = f"https://coins.llama.fi/chart/{chain}:{collat}?start={start_timestamp}&span={span}&period=4h"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
    prices_data = data["coins"].get(f"{chain}:{collat}", {}).get("prices", [])
    return [
        DecimalTimeSeries(value=entry["price"], timestamp=entry["timestamp"])
        for entry in prices_data
    ]


@cached(ttl=300, cache=Cache.MEMORY)
async def get_oracle_prices(
    collateral_id: int, period: Period
) -> list[DecimalTimeSeries]:
    start_timestamp = apply_period(period)

    query = (
        select([PriceRecord.price, PriceRecord.block_timestamp])
        .where(
            and_(
                PriceRecord.collateral_id == collateral_id,
                PriceRecord.block_timestamp >= start_timestamp,
            )
        )
        .order_by(PriceRecord.block_timestamp)
    )
    results = await db.fetch_all(query)
    return [
        DecimalTimeSeries(
            value=result["price"], timestamp=result["block_timestamp"]
        )
        for result in results
    ]


@cached(ttl=3600, cache=Cache.MEMORY)
async def get_gecko_supply(chain: str, token: str) -> float:
    url = f"https://api.coingecko.com/api/v3/coins/{chain}/contract/{token}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                return float(data["market_data"]["total_supply"])
    except Exception as e:
        logger.error(f"Error fetching supply from coingecko: {e}")
        return 0


@cached(ttl=3600, cache=Cache.MEMORY)
async def get_lsd_share(token: str) -> float:
    token_to_dl_slug = {
        CBETH: "Coinbase Wrapped Staked ETH",
        RETH: "Rocket Pool",
        SFRXETH: "Frax Ether",
        WSTETH: "Lido",
    }
    url = f"https://defillama-datasets.llama.fi/lite/protocols2?b=2"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        protocol_data = {
            p["name"]: p["tvl"]
            for p in data["protocols"]
            if p["category"] == "Liquid Staking"
        }
        total = sum(protocol_data.values())
        mshares = {k: v / total * 100 for k, v in protocol_data.items()}
        return mshares[token_to_dl_slug[token.lower()]]
    except Exception as e:
        logger.error(f"Error fetching market share from DL: {e}")
        return 0.0
