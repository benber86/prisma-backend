import asyncio
import json
import logging
from decimal import Decimal

import aiohttp
from sqlalchemy import select

from database.engine import db, wrap_dbs
from database.models.troves import Collateral
from services.celery import celery
from services.messaging.redis import get_redis_client
from utils.const import CHAINS

COL_IMPACT_SLUG = "collateral_impact"
logger = logging.getLogger()
headers = {"accept": "application/json", "Content-Type": "application/json"}


async def get_cowswap_quote(sell_token: str, sell_amount: Decimal) -> Decimal:
    url = "https://api.cow.fi/mainnet/api/v1/quote"
    params = {
        "sellToken": sell_token,
        "buyToken": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "receiver": "0x0000000000000000000000000000000000000000",
        "appData": '{"version":"0.9.0","metadata":{}}',
        "appDataHash": "0xc990bae86208bfdfba8879b64ab68da5905e8bb97aa3da5c701ec1183317a6f6",
        "partiallyFillable": False,
        "sellTokenBalance": "erc20",
        "buyTokenBalance": "erc20",
        "from": "0x0000000000000000000000000000000000000000",
        "signingScheme": "eip712",
        "onchainOrder": False,
        "kind": "sell",
        "sellAmountBeforeFee": str(sell_amount),
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, data=json.dumps(params)
        ) as response:
            try:
                data = await response.json()
                bought = sell_amount - Decimal(data["quote"]["feeAmount"])
                return (
                    Decimal(data["quote"]["buyAmount"]) / bought
                    if bought != 0
                    else Decimal(0)
                )
            except Exception as e:
                logger.error(
                    f"Error fetching cowswap quote for token {sell_token}: {e}"
                )
                return Decimal(0)


async def get_1inch_quote(sell_token: str, sell_amount: Decimal) -> Decimal:
    if sell_amount == 0:
        return Decimal(0)
    url = "https://api-defillama.1inch.io/v5.2/1/quote"
    params = {
        "src": sell_token,
        "dst": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "amount": str(sell_amount),
        "includeGas": "false",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                return Decimal(data["toAmount"]) / sell_amount
    except Exception as e:
        logger.error(
            f"Error fetching cowswap quote for token {sell_token}: {e}"
        )
        return Decimal(0)


async def get_paraswap_quote(
    sell_token: str, sell_amount: Decimal, sell_decimals: int = 18
) -> Decimal:
    if sell_amount != 0:
        return Decimal(0)
    url = "https://apiv5.paraswap.io/prices/"
    params = {
        "srcToken": sell_token,
        "destToken": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "amount": str(sell_amount),
        "srcDecimals": str(sell_decimals),
        "destDecimals": "18",
        "partner": "llamaswap",
        "side": "SELL",
        "network": "1",
        "excludeDEXS": "ParaSwapPool,ParaSwapLimitOrders",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                return Decimal(data["priceRoute"]["destAmount"]) / sell_amount
    except Exception as e:
        logger.error(
            f"Error fetching cowswap quote for token {sell_token}: {e}"
        )
        return Decimal(0)


async def get_best_price(sell_token: str, sell_amount: Decimal) -> Decimal:
    cow, inch, para = await asyncio.gather(
        get_cowswap_quote(sell_token, sell_amount),
        get_1inch_quote(sell_token, sell_amount),
        get_paraswap_quote(sell_token, sell_amount),
    )
    return min([_ for _ in [cow, inch, para] if _ > 0])


async def get_price_impacts(chain: str):
    chain_id = CHAINS[chain]
    amounts = [
        Decimal(a * 10**18)
        for a in [
            0.1,
            100,
            500,
            1000,
            5000,
            10000,
            50000,
            75000,
            100000,
            150000,
        ]
    ]
    collateral_query = select(
        [Collateral.address, Collateral.latest_price]
    ).where(Collateral.chain_id == chain_id)
    collateral_results = await db.fetch_all(collateral_query)

    redis = await get_redis_client("celery")

    for collateral in collateral_results:
        prices = [Decimal(0)]
        impacts = [Decimal(0)]
        for i, amount in enumerate(amounts):
            price = await get_best_price(collateral["address"], amount)
            if price == 0:
                logger.error(
                    f"Error price for amount: {amount} for token: {amount} was 0"
                )
                continue
            prices.append(price)
            impacts += [(price - prices[1]) / prices[1]]
        usd_amounts = [
            float(amount) * float(collateral["latest_price"])
            for amount in [Decimal(0), *amounts]
        ]
        res = [
            {"amount": usd_amounts[i] * 1e-18, "impact": float(impact) * -100}
            for i, impact in enumerate(impacts)
        ]
        await redis.set(
            f"{COL_IMPACT_SLUG}_{chain}_{collateral['address'].lower()}",
            json.dumps(res),
        )


@celery.task
def get_impact_data(chain: str):
    asyncio.run(
        wrap_dbs(get_price_impacts)(
            chain,
        )
    )
