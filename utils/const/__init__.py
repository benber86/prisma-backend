import web3

from .chains import ethereum

CHAINS: dict[str, int] = {ethereum.CHAIN_NAME: ethereum.CHAIN_ID}

SUBGRAPHS: dict[str, str] = {ethereum.CHAIN_NAME: ethereum.SUBGRAPH}

STABLECOINS: dict[str, str] = {ethereum.CHAIN_NAME: ethereum.STABLECOIN}

LABELS: dict[str, dict[str, str]] = {ethereum.CHAIN_NAME: ethereum.LABELS}

CURVE_SUBGRAPHS: dict[str, str] = {
    ethereum.CHAIN_NAME: ethereum.CURVE_SUBGRAPH
}

PROVIDERS: dict[str, web3.HTTPProvider] = {
    ethereum.CHAIN_NAME: ethereum.PROVIDER
}

CBETH = "0xbe9895146f7af43049ca1c1ae358b0541ea49704"
SFRXETH = "0xac3e018457b222d93114458476f3e3416abbe38f"
RETH = "0xae78736cd615f374d3085123a210448e74fc6393"
WSTETH = "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0"
