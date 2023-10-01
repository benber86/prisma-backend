from web3 import Web3

from settings.config import settings

CHAIN_NAME = "ethereum"
CHAIN_ID = 1
SUBGRAPH = "https://api.thegraph.com/subgraphs/name/benber86/prisma"
STABLECOIN = "0x4591DBfF62656E7859Afe5e45f6f47D3669fBB28"
LABELS = {
    "0xed8B26D99834540C5013701bB3715faFD39993Ba": "Stability Pool",
    "0x0CFe5C777A7438C9Dd8Add53ed671cEc7A5FAeE5": "Curve FRAX/mkUSD Pool",
    "0x3de254A0f838a844F727fee81040e0FA7884B935": "Curve crvUSD/mkUSD Pool",
    "0xfdCE0267803C6a0D209D3721d2f01Fd618e9CBF8": "Fee Receiver",
    "0xE0598D793bAf7b4f49F4a003885E4180B28caB61": "Gas Pool",
    "0xc89570207c5BA1B0E3cD372172cCaEFB173DB270": "Curve ETH/mkUSD Pool",
}
CURVE_SUBGRAPH = (
    "https://api.thegraph.com/subgraphs/name/convex-community/volume-mainnet"
)
PROVIDER = Web3.HTTPProvider(
    f"https://eth-mainnet.g.alchemy.com/v2/{settings.ALCHEMY_API_KEY}",
    request_kwargs={"timeout": settings.WEB3_REQUEST_TIMEOUT},
)
