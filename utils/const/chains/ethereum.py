from web3 import Web3

from settings.config import settings

CHAIN_NAME = "ethereum"
CHAIN_ID = 1
SUBGRAPH = f"https://gateway-arbitrum.network.thegraph.com/api/{settings.SUBGRAPH_API_KEY}/subgraphs/id/F83FT8qLMwt8n7n9JmcrJKFZp8D9sWeFH3iYdgXFWSDp"
STABLECOIN = "0x4591DBfF62656E7859Afe5e45f6f47D3669fBB28"
LABELS = {
    "0xed8B26D99834540C5013701bB3715faFD39993Ba": "Stability Pool",
    "0x0CFe5C777A7438C9Dd8Add53ed671cEc7A5FAeE5": "Curve FRAX/mkUSD Pool",
    "0x3de254A0f838a844F727fee81040e0FA7884B935": "Curve crvUSD/mkUSD Pool",
    "0xfdCE0267803C6a0D209D3721d2f01Fd618e9CBF8": "Fee Receiver",
    "0xE0598D793bAf7b4f49F4a003885E4180B28caB61": "Gas Pool",
    "0xc89570207c5BA1B0E3cD372172cCaEFB173DB270": "Curve ETH/mkUSD Pool",
}
START_TIME = 1691625600
CURVE_SUBGRAPH = f"https://subgraph.satsuma-prod.com/{settings.ALCHEMY_SUBGRAPH_KEY}/curve-1/volume-mainnet/api"
CVXPRISMA_SUBGRAPH = f"https://gateway-arbitrum.network.thegraph.com/api/{settings.SUBGRAPH_API_KEY}/subgraphs/id/2WVR8gRct7trp1v1YdaRQXMmHngDiFugwu8NT38ksRMy"
PROVIDER = Web3.HTTPProvider(
    f"https://eth-mainnet.g.alchemy.com/v2/{settings.ALCHEMY_API_KEY}",
    request_kwargs={"timeout": settings.WEB3_REQUEST_TIMEOUT},
)
RECEIVER_MAPPINGS = {
    0: "Stability Pool",
    1: "Wrapped liquid staked Ether 2.0 (Debt)",
    2: "Wrapped liquid staked Ether 2.0 (Mint)",
    3: "Rocket Pool ETH (Debt)",
    4: "Rocket Pool ETH (Mint)",
    5: "Coinbase Wrapped Staked ETH (Debt)",
    6: "Coinbase Wrapped Staked ETH (Mint)",
    7: "Staked Frax Ether (Debt)",
    8: "Staked Frax Ether (Mint)",
    9: "mkUSD/FRAXBP Curve",
    10: "mkUSD/FRAXBP Convex",
    11: "mkUSD/crvUSD Convex",
    12: "mkUSD/crvUSD Curve",
    13: "mkUSD/ETH Curve",
    14: "mkUSD/ETH Convex",
    15: "PRISMA/ETH Curve",
    16: "PRISMA/ETH Convex",
    17: "cvxPRISMA/PRISMA Convex",
    18: "mkUSD/PRISMA Curve",
    19: "mkUSD/PRISMA Convex",
    20: "yPRISMA/PRISMA Curve",
    21: "yPRISMA/PRISMA Convex",
    22: "mkUSD/USDC Curve",
    23: "mkUSD/USDC Convex",
}
