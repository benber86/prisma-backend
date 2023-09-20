from datetime import datetime

from api.models.common import Period

SECONDS_IN_DAY = 24 * 60 * 60


def apply_period(period: Period) -> int:
    current_timestamp = datetime.now().timestamp()

    if period == Period.month:
        start_timestamp = current_timestamp - 30 * SECONDS_IN_DAY
    elif period == Period.semester:
        start_timestamp = current_timestamp - 6 * 30 * SECONDS_IN_DAY
    else:
        start_timestamp = 0
    return int(start_timestamp)
