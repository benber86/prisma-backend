import json
import logging
import time

import requests
from hexbytes import HexBytes
from web3 import Web3
from web3_input_decoder import decode_function
from web3_input_decoder.utils import get_selector_to_function_type

from settings.config import settings

logger = logging.getLogger()


def get_abi(pool_address: str) -> list[dict] | None:
    for i in range(3):
        url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={pool_address}&apikey={settings.ETHERSCAN_TOKEN}"
        abi_response = requests.get(url).json()
        if abi_response["status"] == "1":
            return json.loads(abi_response["result"])
        else:
            time.sleep(5)
    return None


def format_inputs(inputs):
    res = []
    for arg in inputs:
        if arg[0] == "address":
            res.append((arg[0], arg[1], Web3.to_checksum_address(arg[2])))
        elif arg[0] == "bytes":
            res.append((arg[0], arg[1], arg[2].hex()))
        else:
            res.append(arg)
    return res


def decode_call_data(contract: str, calldata: str) -> str:
    abi = get_abi(contract)
    try:
        script = HexBytes(calldata)
        fn = get_selector_to_function_type(abi).get(script[:4])["name"]  # type: ignore
        inputs = decode_function(abi, script)
        return f"Call:\n ├─ To: {Web3.to_checksum_address(contract)}\n ├─ Function: {fn}\n └─ Inputs: {inputs!r}"
    except Exception as e:
        logger.error(f"Unable to parse call data: {calldata} \n{e}")
        return f"Call:\n ├─ To: {Web3.to_checksum_address(contract)}\n └─ Calldata: {calldata!r}"


def decode_payload(payload: list[dict[str, str]]) -> str:
    res = []
    for load in payload:
        res.append(decode_call_data(load["target"], load["data"]))
    return "\n".join(res)
