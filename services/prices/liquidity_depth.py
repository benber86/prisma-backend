import asyncio
import json
import logging

import numpy as np
from pydantic import BaseModel
from web3 import Web3
from web3mc import Multicall

from services.celery import celery
from services.messaging.redis import get_redis_client
from utils.const import CURVE_SUBGRAPHS, PROVIDERS, STABLECOINS
from utils.sims.curve.metapool import CurveMetaPool
from utils.sims.curve.pool import CurvePool
from utils.subgraph.query import async_grt_query

logger = logging.getLogger()


GRAPH_QUERY = """
{
  pools(where:{name_contains_nocase:"mkusd" assetType: 0}) {
    address
    name
    metapool
    basePool
    coinDecimals
    coinNames
    coins
    dailyPoolSnapshots(first: 1 orderBy: timestamp orderDirection: desc) {
      A
      tvl
      fee
    }
  }
}
"""

GRAPH_BASEPOOL_QUERY = """
{
  pools(where:{id:"%s" assetType: 0}) {
    address
    name
    coinDecimals
    coinNames
    coins
    dailyPoolSnapshots(first: 1 orderBy: timestamp orderDirection: desc) {
      A
      tvl
      fee
    }
  }
}
"""

BALANCES_ABI = [
    {
        "stateMutability": "view",
        "type": "function",
        "name": "balances",
        "inputs": [{"name": "arg0", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}],
        "gas": 3153,
    }
]

DEPTH_SLUG = "liquidity_depth"


class PoolSales(BaseModel):
    amounts: list[float]
    prices: list[float]


class PoolDepth(BaseModel):
    name: str
    address: str
    tokens: list[str]
    bid: PoolSales
    ask: PoolSales


class PoolDetails(BaseModel):
    name: str
    address: str
    decimals: list[int]
    coin_names: list[str]
    mkusd_index: int
    A: int
    metapool: bool
    basepool: str | None
    fee: int
    balances: list[int] | None


async def _get_base_pool_info(chain: str, address: str) -> PoolDetails | None:
    query = GRAPH_BASEPOOL_QUERY % address
    data = await async_grt_query(CURVE_SUBGRAPHS[chain], query)
    if data is None:
        logger.error("No base pool data for {} on {}", [address, chain])
        return None
    pool = data["pools"][0]
    snapshot = pool["dailyPoolSnapshots"][0]
    return PoolDetails(
        address=pool["address"],
        name=pool["name"],
        coin_names=pool["coinNames"],
        mkusd_index=-1,
        decimals=pool["coinDecimals"],
        metapool=False,
        basepool=None,
        A=snapshot["A"],
        fee=int(float(snapshot["fee"]) * 1e10),
    )


async def _get_all_relevant_pools(chain: str) -> list[PoolDetails]:
    data = await async_grt_query(CURVE_SUBGRAPHS[chain], GRAPH_QUERY)
    res: list[PoolDetails] = []
    if not data:
        logger.error(f"Failed to retrieve relevant mkUSD pools on {chain}")
        return []

    for pool in data["pools"]:
        snapshot = pool["dailyPoolSnapshots"][0]
        if STABLECOINS[chain].lower() not in pool["coins"]:
            continue
        if float(snapshot["tvl"]) < 50000:
            continue
        res.append(
            PoolDetails(
                address=pool["address"],
                name=pool["name"],
                coin_names=pool["coinNames"],
                mkusd_index=pool["coins"].index(STABLECOINS[chain].lower()),
                decimals=pool["coinDecimals"],
                metapool=pool["metapool"],
                basepool=pool["basePool"] if pool["metapool"] else None,
                A=snapshot["A"],
                fee=int(float(snapshot["fee"]) * 1e10),
            )
        )
    return res


async def get_pool_balances(
    chain: str, pool_details: PoolDetails
) -> list[int]:
    w3 = PROVIDERS[chain]
    contract = Web3(w3).eth.contract(
        Web3.to_checksum_address(pool_details.address), abi=BALANCES_ABI
    )
    multicall = Multicall(provider_url=w3.endpoint_uri, max_retries=1)
    calls = [
        contract.functions.balances(i)
        for i in range(len(pool_details.decimals))
    ]
    bals = await multicall.async_aggregate(calls, use_try=True)
    normalized_balances = [
        bal * (10 ** (18 - pool_details.decimals[i]))
        for i, bal in enumerate(bals)
    ]
    return normalized_balances


def get_depth(
    pool: CurvePool,
    max_amount: int,
    mkusd_index: int,
    other_index: int,
    buy: bool,
) -> PoolSales:
    depth = PoolSales(prices=[], amounts=[], bid=buy)
    levels = np.linspace(1e18, max_amount, 100)
    for i, level in enumerate(levels):
        level = int(level)
        if buy:
            price = level / pool.get_dy(other_index, mkusd_index, level)
        else:
            price = pool.get_dy(mkusd_index, other_index, level) / level
        depth.prices.append(price)
        depth.amounts.append(level * 1e-18)
    return depth


def get_metapool_depth(
    pool: CurveMetaPool,
    max_amount: int,
    mkusd_index: int,
    other_index: int,
    buy: bool,
) -> PoolSales:
    depth = PoolSales(prices=[], amounts=[], bid=buy)
    levels = np.linspace(1e18, max_amount, 100)
    for i, level in enumerate(levels):
        level = int(level)
        if buy:
            price = level / pool.get_dy_underlying(
                other_index, mkusd_index, level
            )
        else:
            price = (
                pool.get_dy_underlying(mkusd_index, other_index, level) / level
            )
        depth.prices.append(price)
        depth.amounts.append(level * 1e-18)
    return depth


async def handle_stable_pool(
    chain: str,
    pool_details: PoolDetails,
) -> list[PoolDepth]:
    pool_details.balances = await get_pool_balances(chain, pool_details)
    pool = CurvePool(
        A=pool_details.A,
        D=pool_details.balances,
        n=len(pool_details.decimals),
        fee=pool_details.fee,
    )

    ask = get_depth(
        pool=pool,
        mkusd_index=pool_details.mkusd_index,
        other_index=1 - pool_details.mkusd_index,
        max_amount=max(pool_details.balances),
        buy=False,
    )

    bid = get_depth(
        pool=pool,
        mkusd_index=pool_details.mkusd_index,
        other_index=1 - pool_details.mkusd_index,
        max_amount=max(pool_details.balances),
        buy=True,
    )

    return [
        PoolDepth(
            address=pool_details.address,
            name=pool_details.name,
            tokens=[
                pool_details.coin_names[pool_details.mkusd_index],
                pool_details.coin_names[1 - pool_details.mkusd_index],
            ],
            ask=ask,
            bid=bid,
        )
    ]


async def handle_metapool(
    chain: str, metapool_details: PoolDetails
) -> list[PoolDepth]:
    metapool_details.balances = await get_pool_balances(
        chain, metapool_details
    )
    if not metapool_details.basepool:
        logger.error("No base pool associated to metapool")
        return []

    basepool_details = await _get_base_pool_info(
        chain, metapool_details.basepool
    )
    if not basepool_details:
        return []
    basepool_details.balances = await get_pool_balances(
        chain, basepool_details
    )

    sim_basepool = CurvePool(
        A=basepool_details.A,
        D=basepool_details.balances,
        n=len(basepool_details.decimals),
        fee=basepool_details.fee,
    )
    sim_metapool = CurveMetaPool(
        A=metapool_details.A,
        D=metapool_details.balances,
        n=len(metapool_details.decimals),
        fee=metapool_details.fee,
        basepool=sim_basepool,
    )
    res: list[PoolDepth] = []

    for i in range(len(basepool_details.decimals)):
        coin_index = i + 1
        coins = [
            metapool_details.coin_names[0],
            basepool_details.coin_names[i],
        ]
        bid = get_metapool_depth(
            pool=sim_metapool,
            mkusd_index=0,
            other_index=coin_index,
            max_amount=max(metapool_details.balances),
            buy=True,
        )
        ask = get_metapool_depth(
            pool=sim_metapool,
            mkusd_index=0,
            other_index=coin_index,
            max_amount=max(metapool_details.balances),
            buy=False,
        )
        res.append(
            PoolDepth(
                address=metapool_details.address,
                name=metapool_details.name,
                tokens=coins,
                ask=ask,
                bid=bid,
            )
        )
    return res


async def update_depth_charts(chain: str):
    pools = await _get_all_relevant_pools(chain)
    res: list[PoolDepth] = []
    for pool in pools:
        logger.info(f"Getting depth chart data for pool {pool}")
        if pool.metapool:
            res += await handle_metapool(chain, pool)
        else:
            res += await handle_stable_pool(chain, pool)
    redis = await get_redis_client("celery")
    await redis.set(
        f"{DEPTH_SLUG}_{chain}", json.dumps([r.dict() for r in res])
    )


@celery.task
def get_depth_data(chain: str):
    asyncio.run(update_depth_charts(chain))
