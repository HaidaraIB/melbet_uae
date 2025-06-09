from client.client_calls.constants import PICKLE_FILE, SessionState
import pickle
import os
from datetime import datetime, timezone
import logging

log = logging.getLogger(__name__)


def save_session_data():
    global session_data
    with open(PICKLE_FILE, "wb") as f:
        pickle.dump(session_data, f)


def load_session_data():
    """Load session_data from pickle file if it exists."""
    global session_data
    if os.path.exists(PICKLE_FILE):
        try:
            with open(PICKLE_FILE, "rb") as f:
                session_data = pickle.load(f)
            log.info(f"Loaded previous session data from {PICKLE_FILE}")
        except (pickle.PickleError, EOFError) as e:
            log.error(f"Error loading session data: {e}")
            session_data = {}


def clear_session_data(user_id: int):
    global session_data
    del session_data[user_id]


def initialize_user_session_data(user_id: int, session_type: str):
    global session_data
    session_data[user_id] = {
        "state": SessionState.AWAITING_RECEIPT.name,
        "type": session_type,
        "data": {
            "amount": None,
            "transaction_id": None,
            "payment_method": None,
            "date": None,
            "extracted_text": None,
        },
        "metadata": {
            "required_fields": ["amount", "transaction_id", "payment_method"],
            "optional_fields": ["date"],
            "missing_fields": [],
        },
    }
    save_session_data()


def now_iso() -> datetime:
    return datetime.now(timezone.utc)


def classify_intent(text: str):
    t = (text or "").lower()
    if any(k in t for k in ("dp", "deposit", "ايداع", "إيداع")):
        return "deposit"
    if any(k in t for k in ("wd", "withdraw", "سحب")):
        return "withdraw"
    return None


session_data = {}
load_session_data()
