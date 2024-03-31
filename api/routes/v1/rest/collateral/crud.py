import logging
from datetime import datetime
from operator import and_

import aiohttp
from aiocache import Cache, cached
from sqlalchemy import func, select

from api.models.common import DecimalTimeSeries, Pagination, Period
from api.routes.utils.time import apply_period
from api.routes.v1.rest.collateral.models import (
    OrderFilter,
    StakeZapInfo,
    StakeZapResponse,
)
from database.engine import db
from database.models.troves import Collateral, PriceRecord, ZapStakes
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
        CBETH.lower(): "Coinbase Wrapped Staked ETH",
        RETH.lower(): "Rocket Pool",
        SFRXETH.lower(): "Frax Ether",
        WSTETH.lower(): "Lido",
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


async def get_zaps(
    chain_id: int,
    collateral_id: int,
    pagination: Pagination,
    order: OrderFilter,
) -> StakeZapResponse:
    base_query = (
        select(
            [
                ZapStakes.amount,
                ZapStakes.block_timestamp,
                ZapStakes.block_number,
                ZapStakes.transaction_hash,
            ]
        )
        .join(Collateral, ZapStakes.collateral_id == Collateral.id)
        .where(
            ZapStakes.collateral_id == collateral_id,
            Collateral.chain_id == chain_id,
        )
    )

    order_column = getattr(ZapStakes, order.order_by)  # type: ignore
    if order.desc:
        base_query = base_query.order_by(order_column.desc())
    else:
        base_query = base_query.order_by(order_column)

    items_per_page = pagination.items
    offset = (pagination.page - 1) * items_per_page
    paginated_query = base_query.limit(items_per_page).offset(offset)

    paginated_results = await db.fetch_all(paginated_query)

    zaps = [
        StakeZapInfo(
            amount=float(result.amount) * 1e-18,
            block_timestamp=int(result.block_timestamp),
            block_number=int(result.block_number),
            tx_hash=result.transaction_hash,
        )
        for result in paginated_results
    ]

    count_and_sum_query = select(
        [
            func.count().label("total_count"),
            func.sum(ZapStakes.amount).label("total_amount"),
        ]
    ).where(
        ZapStakes.collateral_id == collateral_id,
        Collateral.chain_id == chain_id,
    )

    count_and_sum_result = await db.fetch_one(count_and_sum_query)
    total_count = count_and_sum_result.total_count
    total_amount = (
        float(count_and_sum_result.total_amount) * 1e-18
        if count_and_sum_result.total_amount is not None
        else 0
    )

    return StakeZapResponse(
        zaps=zaps, count=total_count, total_amount=total_amount
    )
