import asyncio
import json
import time

import aiohttp
from web3 import Web3

from services.celery import celery
from services.messaging.redis import get_redis_client
from settings.config import settings
from utils.const import CHAINS, LABELS

url = "https://api-v2.flipsidecrypto.xyz/json-rpc"
API_KEY = settings.FLIPSIDE_API_KEY
HOLDERS_SLUG = "mkusd_holders"

headers = {"x-api-key": f"{API_KEY}", "Content-Type": "application/json"}


async def _run_holders_query() -> str:
    data = {
        "jsonrpc": "2.0",
        "method": "createQueryRun",
        "params": [
            {
                "resultTTLHours": 1,
                "maxAgeMinutes": 0,
                "sql": """
                    WITH Top5Balances AS (
                        SELECT SUM(current_bal) as top5_total_balance
                        FROM (
                            SELECT current_bal
                            FROM ethereum.core.ez_current_balances
                            WHERE contract_address = LOWER('0x4591dbff62656e7859afe5e45f6f47d3669fbb28')
                            ORDER BY usd_value_now DESC
                            LIMIT 5
                        )
                    ),
                    TotalBalance AS (
                        SELECT SUM(current_bal) as total_balance
                        FROM ethereum.core.ez_current_balances
                        WHERE contract_address = LOWER('0x4591dbff62656e7859afe5e45f6f47d3669fbb28')
                    )
                    SELECT last_activity_block_timestamp::date as date,
                           current_bal,
                           user_address,
                           (SELECT total_balance FROM TotalBalance) - (SELECT top5_total_balance FROM Top5Balances) as remaining_balance
                    FROM ethereum.core.ez_current_balances
                    WHERE contract_address = LOWER('0x4591dbff62656e7859afe5e45f6f47d3669fbb28')
                    ORDER BY usd_value_now DESC
                    LIMIT 5;
                """,
                "tags": {"source": "postman-demo", "env": "test"},
                "dataSource": "snowflake-default",
                "dataProvider": "flipside",
            }
        ],
        "id": 1,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, data=json.dumps(data)
        ) as response:
            result = await response.json()
            return result["result"]["queryRun"]["id"]


async def _check_query_status(query_run_id: str):
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "getQueryRun",
            "params": [{"queryRunId": f"{query_run_id}"}],
            "id": 1,
        }
    )
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, data=payload
        ) as response:
            result = await response.json()
            return result["result"]["queryRun"]["state"]


async def _get_query_results(
    query_run_id: str, chain: str
) -> list[dict[str, float | str]]:
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "getQueryRunResults",
            "params": [
                {
                    "queryRunId": f"{query_run_id}",
                    "format": "json",
                    "page": {"number": 1, "size": 10},
                }
            ],
            "id": 1,
        }
    )

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, data=payload
        ) as response:
            data = await response.json()

    def _format_address(address: str, chain_name: str):
        checksumed_address = Web3.to_checksum_address(address)
        if checksumed_address in LABELS[chain_name]:
            return LABELS[chain_name][checksumed_address]
        return checksumed_address

    res = [
        {
            "value": r["current_bal"],
            "label": _format_address(r["user_address"], chain),
        }
        for r in data["result"]["rows"]
    ]

    res.append(
        {
            "value": data["result"]["rows"][0]["remaining_balance"],
            "label": "Others",
        }
    )

    return res


async def update_holders(chain: str):
    query_run_id = await _run_holders_query()
    attempts = 0
    while True:
        status = await _check_query_status(query_run_id)
        if status == "QUERY_STATE_SUCCESS":
            break
        elif attempts > 10:
            return
        attempts += 1
        time.sleep(5)
    holders = await _get_query_results(query_run_id, chain)
    redis = await get_redis_client("celery")
    await redis.set(f"{HOLDERS_SLUG}_{chain}", json.dumps(holders))


@celery.task
def get_holder_data(chain: str):
    asyncio.run(update_holders(chain))
