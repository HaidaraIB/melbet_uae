from datetime import datetime
from common.constants import TIMEZONE
import math

def calc_from_to_dates_and_duration_in_days(duration_type: str, duration_value: str):
    now = datetime.now(TIMEZONE)
    if duration_type == "hours":
        hours = duration_value
        duration_in_days = math.ceil(hours / 24)
    else:
        days = duration_value
        duration_in_days = days

    return now, duration_in_days
