from datetime import datetime

from api.models.common import Period

SECONDS_IN_DAY = 24 * 60 * 60


def apply_period(period: Period) -> int:
    current_timestamp = datetime.utcnow().timestamp()

    if period == Period.week.value:
        start_timestamp = current_timestamp - 7 * SECONDS_IN_DAY
    elif period == Period.month.value:
        start_timestamp = current_timestamp - 30 * SECONDS_IN_DAY
    elif period == Period.trimester.value:
        start_timestamp = current_timestamp - 3 * 30 * SECONDS_IN_DAY
    elif period == Period.semester.value:
        start_timestamp = current_timestamp - 6 * 30 * SECONDS_IN_DAY
    else:
        start_timestamp = 0
    return int(start_timestamp)
