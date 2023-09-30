from .chains import ethereum

CHAINS: dict[str, int] = {ethereum.CHAIN_NAME: ethereum.CHAIN_ID}

SUBGRAPHS: dict[str, str] = {ethereum.CHAIN_NAME: ethereum.SUBGRAPH}

STABLECOINS: dict[str, str] = {ethereum.CHAIN_NAME: ethereum.STABLECOIN}

LABELS: dict[str, dict[str, str]] = {ethereum.CHAIN_NAME: ethereum.LABELS}
