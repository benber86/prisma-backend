import json
import os

location = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__))
)
MKUSD_ABI = json.load(open(os.path.join(location, "mkUSD.json"), "r"))
