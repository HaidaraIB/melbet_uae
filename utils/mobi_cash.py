import hashlib
from datetime import datetime, timezone
from Config import Config
import aiohttp
import logging

log = logging.getLogger(__name__)


mobi_values_dict = {
    "uae": {
        "hash": Config.MOBI_CASH_HASH_VALUE_UAE,
        "id": int(Config.MOBI_CASH_CASHDESKID_UAE),
        "pass": Config.MOBI_CASH_CASHIERPASS_UAE,
    },
    "syr": {
        "hash": Config.MOBI_CASH_HASH_VALUE_SYR,
        "id": int(Config.MOBI_CASH_CASHDESKID_SYR),
        "pass": Config.MOBI_CASH_CASHIERPASS_SYR,
    },
}


def sha256(text: str):
    return hashlib.sha256(text.encode()).hexdigest()


def md5(text: str):
    return hashlib.md5(text.encode()).hexdigest()


def get_confirm(val: str, hash_val: str):
    return md5(f"{val}:{hash_val}")


async def deposit(user_id: int, amount: float, country: str):
    step2 = md5(
        f"summa={amount}&cashierpass={mobi_values_dict[country]['pass']}&cashdeskid={mobi_values_dict[country]['id']}"
    )
    step1 = sha256(f"hash={mobi_values_dict[country]['hash']}&lng=en&userid={user_id}")
    sign = sha256(step1 + step2)
    confirm = get_confirm(user_id, mobi_values_dict[country]["hash"])
    headers = {"sign": sign}
    url = f"https://partners.servcul.com/CashdeskBotAPI/Deposit/{user_id}/Add"
    j = {
        "cashdeskid": mobi_values_dict[country]["id"],
        "lng": "en",
        "summa": float(amount),
        "confirm": confirm,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=j, headers=headers) as response:
                data = await response.json()
                return data

    except Exception as e:
        log.error(f"Error in {__name__}.deposit: {e}")
        return False


async def withdraw(user_id: int, code: str, country: str):
    step1 = sha256(f"hash={mobi_values_dict[country]["hash"]}&lng=en&userid={user_id}")
    step2 = md5(
        f"code={code}&cashierpass={mobi_values_dict[country]['pass']}&cashdeskid={mobi_values_dict[country]['id']}"
    )
    sign = sha256(step1 + step2)
    confirm = get_confirm(user_id, mobi_values_dict[country]["hash"])
    headers = {"sign": sign}
    url = f"https://partners.servcul.com/CashdeskBotAPI/Deposit/{user_id}/Payout"
    j = {
        "cashdeskid": mobi_values_dict[country]["id"],
        "lng": "en",
        "code": code,
        "confirm": confirm,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=j, headers=headers) as response:
                data = await response.json()
                return data

    except Exception as e:
        log.error(f"Error in {__name__}.deposit: {e}")
        return False


async def get_balance(country: str):
    dt = datetime.now(timezone.utc).strftime("%Y.%m.%d %H:%M:%S")
    step1 = sha256(
        f"hash={mobi_values_dict[country]['hash']}&cashdeskid={mobi_values_dict[country]['id']}&dt={dt}"
    )
    step2 = md5(
        f"dt={dt}&cashierpass={mobi_values_dict[country]['pass']}&cashdeskid={mobi_values_dict[country]['id']}"
    )
    sign = sha256(step1 + step2)
    confirm = md5(
        f"{mobi_values_dict[country]['id']}:{mobi_values_dict[country]['hash']}"
    )
    headers = {"sign": sign}
    url = f"https://partners.servcul.com/CashdeskBotAPI/Cashdesk/{mobi_values_dict[country]['id']}/Balance"
    params = {"confirm": confirm, "dt": dt}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                data = await response.json()
                return data

    except Exception as e:
        log.error(f"Error in {__name__}.deposit: {e}")
        return False


async def search_user(user_id: int, country: str):
    step1 = sha256(
        f"hash={mobi_values_dict[country]['hash']}&userid={user_id}&cashdeskid={mobi_values_dict[country]['id']}"
    )
    step2 = md5(
        f"userid={user_id}&cashierpass={mobi_values_dict[country]['pass']}&hash={mobi_values_dict[country]['hash']}"
    )
    sign = sha256(step1 + step2)
    confirm = get_confirm(user_id, mobi_values_dict[country]["hash"])
    headers = {"sign": sign}
    url = f"https://partners.servcul.com/CashdeskBotAPI/Users/{user_id}"
    params = {"confirm": confirm, "cashdeskid": mobi_values_dict[country]["id"]}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                data = await response.json()
                return data

    except Exception as e:
        log.error(f"Error in {__name__}.deposit: {e}")
        return False
