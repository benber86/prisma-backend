import logging
import time
from typing import Any, List, Mapping, Optional

import aiohttp
import requests
import requests.exceptions

logger = logging.getLogger()


def grt_query(
    endpoint: str, query: str
) -> Optional[Mapping[str, List[Mapping[str, Any]]]]:
    for i in range(3):
        r = requests.post(endpoint, json={"query": query}, timeout=600)
        try:
            return r.json().get("data", None)
        except (
            requests.exceptions.JSONDecodeError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ):
            logger.error(
                f"Failed at fulfilling request {query} for {endpoint}, retrying ({i}/3)"
            )
            time.sleep(60)
            continue
    return None


async def fetch_data(endpoint: str, query: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            endpoint, json={"query": query}, timeout=600
        ) as response:
            if response.status != 200:
                raise Exception(
                    f"Request failed with status {response.status}"
                )
            return await response.json()


async def async_grt_query(
    endpoint: str, query: str
) -> dict[str, list[dict[str, Any]]] | None:
    for i in range(3):
        r = await fetch_data(endpoint, query)
        try:
            return r.get("data", None)
        except Exception as e:
            logger.error(
                f"Failed at fulfilling request {query} for {endpoint}: {e}, retrying ({i}/3)"
            )
            time.sleep(60)
            continue
    return None
