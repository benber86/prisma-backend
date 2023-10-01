from datetime import datetime

import aiohttp
from aiocache import Cache, cached
from sqlalchemy import Integer, and_, bindparam, select, text
from web3 import Web3

from api.models.common import DecimalTimeSeries, IntegerLabelledSeries, Period
from api.routes.utils.time import SECONDS_IN_DAY, apply_period
from database.engine import db
from database.models.common import StableCoinPrice
from services.prices.liquidity_depth import PoolDepth, PoolSales
from utils.const import PROVIDERS, STABLECOINS
from utils.const.abis import MKUSD_ABI


@cached(ttl=300, cache=Cache.MEMORY)
async def get_price_history(
    chain_id: int, period: Period
) -> list[DecimalTimeSeries]:
    start_timestamp = apply_period(period)
    query = (
        select([StableCoinPrice.price, StableCoinPrice.timestamp])
        .where(
            and_(
                StableCoinPrice.chain_id == chain_id,
                StableCoinPrice.timestamp >= start_timestamp,
            )
        )
        .order_by(StableCoinPrice.timestamp)
    )

    results = await db.fetch_all(query)
    return [
        DecimalTimeSeries(value=result["price"], timestamp=result["timestamp"])
        for result in results
    ]


@cached(ttl=300, cache=Cache.MEMORY)
async def get_price_histogram(
    chain_id: int, bins: int, period: Period
) -> list[IntegerLabelledSeries]:

    start_timestamp = apply_period(period)

    query = text(
        """
        SELECT
            count(*) as bin_count,
            min(price) as bin_min,
            max(price) as bin_max
        FROM
            (
                SELECT
                    width_bucket(price, min_price, max_price, :bins) as bin,
                    price
                FROM
                    mkusd_price,
                    (
                        SELECT
                            min(price) as min_price,
                            max(price) as max_price
                        FROM
                            mkusd_price
                        WHERE
                            chain_id = :chain_id AND
                            timestamp >= :start_timestamp
                    ) as stats
                WHERE
                    chain_id = :chain_id AND
                    timestamp >= :start_timestamp
            ) as binned_data
        GROUP BY
            bin
        ORDER BY
            bin_min;
    """
    )

    query = query.bindparams(
        bindparam("chain_id", value=chain_id, type_=Integer),
        bindparam("bins", value=bins, type_=Integer),
        bindparam("start_timestamp", value=start_timestamp, type_=Integer),
    )

    results = await db.fetch_all(query)

    return [
        IntegerLabelledSeries(
            value=int(result["bin_count"]),
            label=f"[{result['bin_min']}, {result['bin_max']})",
        )
        for result in results
    ]


def _find_threshold(asks: PoolSales):
    for i, price in enumerate(asks.prices):
        pct = (price - asks.prices[0]) / price
        if pct < -0.02:
            return asks.amounts[i]
    return 0


@cached(ttl=300, cache=Cache.MEMORY)
async def get_two_percent(data: list[PoolDepth]) -> float:
    total = 0
    for i, pool in enumerate(data):
        if (i > 0) and (data[i - 1].name == pool.name):
            continue
        total += _find_threshold(pool.ask)
    return total


@cached(ttl=300, cache=Cache.MEMORY)
async def get_circulating_supply(chain: str) -> float:
    w3 = PROVIDERS[chain]
    contract = Web3(w3).eth.contract(
        Web3.to_checksum_address(STABLECOINS[chain]), abi=MKUSD_ABI
    )
    return contract.functions.circulatingSupply().call() * 1e-18


@cached(ttl=300, cache=Cache.MEMORY)
async def get_price(chain: str) -> float:
    url = f"https://prices.curve.fi/v1/usd_price/{chain}/{STABLECOINS[chain]}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
    return data["data"]["usd_price"]


@cached(ttl=300, cache=Cache.MEMORY)
async def get_volume(chain: str, pools: list[str]) -> float:
    total = 0
    current_timestamp = int(datetime.now().timestamp())
    start_timestamp = current_timestamp - SECONDS_IN_DAY
    for pool in pools:
        url = f"https://prices.curve.fi/v1/volume/usd/{chain}/{pool}?interval=day&start={start_timestamp}&end={current_timestamp}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
        total += data["data"][0]["volume"]
    return total
