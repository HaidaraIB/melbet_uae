from enum import Enum, auto


class SessionState(Enum):
    AWAITING_RECEIPT = auto()
    AWAITING_MISSING_FIELDS = auto()
    AWAITING_CONFIRMATION = auto()


PICKLE_FILE = "data/session_data.pkl"
