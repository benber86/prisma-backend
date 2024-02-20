import logging
from datetime import datetime

import aiohttp
import pandas as pd
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

logger = logging.getLogger()


@cached(ttl=300, cache=Cache.MEMORY)
async def get_supply_history(chain_id: int) -> list[DecimalTimeSeries]:
    query = """
    WITH relevant_managers AS (
        SELECT
            id
        FROM
            trove_managers
        WHERE
            chain_id = :chain_id
    ),
    daily_debts AS (
        SELECT
            tms.manager_id,
            tms.total_debt,
            tms.block_timestamp,
            DATE(TO_TIMESTAMP(tms.block_timestamp)) AS snapshot_date,
            ROW_NUMBER() OVER(PARTITION BY tms.manager_id, DATE(TO_TIMESTAMP(tms.block_timestamp)) ORDER BY tms.block_timestamp DESC) AS rn
        FROM
            trove_manager_snapshots tms
        INNER JOIN
            relevant_managers rm ON tms.manager_id = rm.id
    )
    SELECT
        manager_id,
        snapshot_date,
        total_debt
    FROM
        daily_debts
    WHERE
        rn = 1
    ORDER BY
        manager_id, snapshot_date

    """
    results = await db.fetch_all(query, values={"chain_id": chain_id})

    df = pd.DataFrame(
        [
            {
                "snapshot_date": r["snapshot_date"],
                "manager_id": r["manager_id"],
                "total_debt": r["total_debt"],
            }
            for r in results
        ]
    )
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
    df.sort_values("snapshot_date", inplace=True)

    print(df)
    min_date = df["snapshot_date"].min()
    max_date = df["snapshot_date"].max()
    all_dates = pd.date_range(start=min_date, end=max_date, freq="D")
    filled_df = pd.DataFrame()

    for manager_id in df["manager_id"].unique():
        manager_df = df[df["manager_id"] == manager_id].copy()
        manager_df.sort_values("snapshot_date", inplace=True)
        manager_df.set_index("snapshot_date", inplace=True)
        manager_df.index = pd.to_datetime(manager_df.index)
        manager_df = manager_df.reindex(all_dates)
        manager_df.ffill(inplace=True)
        manager_df = manager_df.reset_index().rename(
            columns={"index": "snapshot_date"}
        )
        manager_df["manager_id"] = manager_id

        filled_df = pd.concat([filled_df, manager_df], ignore_index=True)

    print(filled_df.sort_values("snapshot_date"))

    summed_df = (
        filled_df.groupby("snapshot_date")["total_debt"].sum().reset_index()
    )
    summed_df.sort_values("snapshot_date", inplace=True)

    series = [
        DecimalTimeSeries(
            value=row["total_debt"],
            timestamp=int(row["snapshot_date"].timestamp()),
        )
        for index, row in summed_df.iterrows()
    ]

    return series


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
        try:
            if (i > 0) and (data[i - 1].name == pool.name):
                continue
            total += _find_threshold(pool.ask)
        except Exception as e:
            logger.error(
                f"Error calculating liquidity depth for pool {pool}: {e}"
            )
    return total


@cached(ttl=300, cache=Cache.MEMORY)
async def get_circulating_supply(chain: str) -> float:
    try:
        w3 = PROVIDERS[chain]
        contract = Web3(w3).eth.contract(
            Web3.to_checksum_address(STABLECOINS[chain]), abi=MKUSD_ABI
        )
        return contract.functions.circulatingSupply().call() * 1e-18
    except Exception as e:
        logger.error(f"Error fetching circulating supply : {e}")
        return 0


@cached(ttl=300, cache=Cache.MEMORY)
async def get_price(chain: str) -> float:
    url = f"https://prices.curve.fi/v1/usd_price/{chain}/{STABLECOINS[chain]}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
        return data["data"]["usd_price"]
    except Exception as e:
        logging.error(f"Error fetching price from {url}: {e}")
        return 0


@cached(ttl=300, cache=Cache.MEMORY)
async def get_volume(chain: str, pools: list[str]) -> float:
    total = 0
    current_timestamp = int(datetime.utcnow().timestamp())
    start_timestamp = current_timestamp - SECONDS_IN_DAY
    for pool in pools:
        try:
            url = f"https://prices.curve.fi/v1/volume/usd/{chain}/{pool}?interval=day&start={start_timestamp}&end={current_timestamp}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
            total += data["data"][0]["volume"]
        except Exception as e:
            logging.error(
                f"Error getting volume for pool {pool}: {e} - url {url}"
            )
    return total
