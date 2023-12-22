import web3

from .chains import ethereum

CHAINS: dict[str, int] = {ethereum.CHAIN_NAME: ethereum.CHAIN_ID}

SUBGRAPHS: dict[str, str] = {ethereum.CHAIN_NAME: ethereum.SUBGRAPH}

STABLECOINS: dict[str, str] = {ethereum.CHAIN_NAME: ethereum.STABLECOIN}

LABELS: dict[str, dict[str, str]] = {ethereum.CHAIN_NAME: ethereum.LABELS}

START_TIMES: dict[str, int] = {ethereum.CHAIN_NAME: ethereum.START_TIME}

CURVE_SUBGRAPHS: dict[str, str] = {
    ethereum.CHAIN_NAME: ethereum.CURVE_SUBGRAPH
}

CVXPRISMA_SUBGRAPHS: dict[str, str] = {
    ethereum.CHAIN_NAME: ethereum.CVXPRISMA_SUBGRAPH
}

PROVIDERS: dict[str, web3.HTTPProvider] = {
    ethereum.CHAIN_NAME: ethereum.PROVIDER
}
RECEIVER_MAPPINGS: dict[str, dict[int, str]] = {
    ethereum.CHAIN_NAME: ethereum.RECEIVER_MAPPINGS
}

CBETH = "0xbe9895146f7af43049ca1c1ae358b0541ea49704"
SFRXETH = "0xac3e018457b222d93114458476f3e3416abbe38f"
RETH = "0xae78736cd615f374d3085123a210448e74fc6393"
WSTETH = "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0"

YPRISMA_STAKING = "0x774a55C3Eeb79929fD445Ae97191228Ab39c4d0f"
CVXPRISMA_STAKING = "0x0c73f1cFd5C9dFc150C8707Aa47Acbd14F0BE108"
