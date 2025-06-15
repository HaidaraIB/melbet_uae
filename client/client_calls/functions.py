import aiohttp
from Config import Config
from client.client_calls.constants import PICKLE_FILE, SessionState
import pickle
import os
from datetime import datetime, timezone
import json
import models
import logging

log = logging.getLogger(__name__)


def save_session_data():
    global session_data
    with open(PICKLE_FILE, "wb") as f:
        pickle.dump(session_data, f)


def load_session_data():
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
    save_session_data()


def initialize_user_session_data(user_id: int, from_group_id: int, st: str):
    global session_data
    session_data[user_id] = {
        "metadata": {
            "required_deposit_fields": [
                "amount",
                "receipt_id",
                "currency",
            ],
            "optional_deposit_fields": ["date"],
            "required_withdraw_fields": [
                "withdrawal_code",
                "payment_info",
            ],
            "optional_withdraw_fields": [],
            "payment_method": None,
            "stripe_link": None,
            "from_group_id": from_group_id,
        },
    }
    if st == "deposit":
        session_data[user_id]["deposit"] = {
            "state": SessionState.AWAITING_PAYMENT_METHOD.name,
            "data": {
                "amount": None,
                "receipt_id": None,
                "date": None,
                "extracted_text": None,
                "currency": None,
            },
        }
    else:
        session_data[user_id]["withdraw"] = {
            "state": SessionState.AWAITING_PAYMENT_METHOD.name,
            "data": {
                "withdrawal_code": None,
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


async def check_stripe_payment_webhook(uid: int):
    url = f"https://webhook.site/token/{Config.WEBHOOK_TOKEN}/requests"
    headers = {
        "Api-Key": Config.WEBHOOK_API_KEY,
    }
    params = {
        "sorting": "newest",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    for req in data["data"]:
                        try:
                            if not req["user_agent"].lower().startswith("stripe"):
                                continue
                            body = json.loads(req.get("content", ""))
                            if (
                                body["data"]["object"]["metadata"]["telegram_id"]
                                == str(uid)
                                and body["type"] == "payment_intent.succeeded"
                            ):
                                with models.session_scope() as s:
                                    transaction = (
                                        s.query(models.Transaction)
                                        .filter_by(receipt_id=body["data"]["object"]["id"])
                                        .first()
                                    )
                                    if not transaction:
                                        return body
                        except Exception as e:
                            log.error(f"Exception: {e}")
                            continue
        return False

    except Exception as e:
        log.error(f"Exception: {e}")
        return False


session_data = {}
load_session_data()
