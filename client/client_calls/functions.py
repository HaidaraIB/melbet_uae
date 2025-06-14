from client.client_calls.constants import PICKLE_FILE, SessionState
import pickle
import os
from datetime import datetime, timezone
import logging

log = logging.getLogger(__name__)

session_data = {}


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


def clear_session_data(user_id: int, st: str):
    global session_data
    del session_data[user_id][st]
    save_session_data()


def initialize_user_session_data(user_id: int, st: str):
    global session_data
    session_data[user_id] = {
        "metadata": {
            "required_deposit_fields": [
                "amount",
                "transaction_id",
                "payment_method",
                "currency",
            ],
            "optional_deposit_fields": ["date"],
            "required_withdraw_fields": [
                "withdrawal_code",
                "payment_method",
                "payment_info",
            ],
            "optional_withdraw_fields": [],
        },
    }
    if st == "deposit":
        session_data[user_id]["deposit"] = {
            "state": SessionState.AWAITING_MISSING_FIELDS.name,
            "data": {
                "amount": None,
                "transaction_id": None,
                "payment_method": None,
                "date": None,
                "extracted_text": None,
                "currency": None,
                "stripe_link": None,
            },
        }
    else:
        session_data[user_id]["withdraw"] = {
            "state": SessionState.AWAITING_MISSING_FIELDS.name,
            "data": {
                "withdrawal_code": None,
                "payment_method": None,
                "payment_info": None,
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
