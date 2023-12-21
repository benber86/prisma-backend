import time

from utils.const import START_TIMES

WEEK = 60 * 60 * 24 * 7


def get_week(chain: str) -> int:
    return (int(time.time()) - START_TIMES[chain]) // WEEK


def get_first_week(chain: str) -> int:
    return START_TIMES[chain] // WEEK
