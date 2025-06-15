from enum import Enum, auto
from Config import Config


class SessionState(Enum):
    AWAITING_PAYMENT_METHOD = auto()
    AWAITING_PAYMENT = auto()
    AWAITING_RECEIPT = auto()
    AWAITING_MISSING_FIELDS = auto()
    AWAITING_CONFIRMATION = auto()


PICKLE_FILE = "data/session_data.pkl"


STRIPE = "Credit Card"

CURRENCIES = {
    Config.UAE_MONITOR_GROUP_ID: {
        "currency": "aed",
    },
    Config.SYR_MONITOR_GROUP_ID: {
        "currency": "syp",
    },
}
