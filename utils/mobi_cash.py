import hashlib
from datetime import datetime, timezone
from Config import Config
import aiohttp
import logging

log = logging.getLogger(__name__)


def sha256(text: str):
    return hashlib.sha256(text.encode()).hexdigest()


def md5(text: str):
    return hashlib.md5(text.encode()).hexdigest()


def get_confirm(val: str, hash_val: str):
    return md5(f"{val}:{hash_val}")


async def deposit(user_id: int, amount: float):
    step1 = sha256(f"hash={Config.MOBI_CASH_HASH_VALUE}&lng=en&userid={user_id}")
    step2 = md5(
        f"summa={amount}&cashierpass={Config.MOBI_CASH_CASHIERPASS}&cashdeskid={Config.MOBI_CASH_CASHDESKID}"
    )
    sign = sha256(step1 + step2)
    confirm = get_confirm(user_id, Config.MOBI_CASH_HASH_VALUE)
    headers = {"sign": sign}
    url = f"https://partners.servcul.com/CashdeskBotAPI/Deposit/{user_id}/Add"
    j = {
        "cashdeskid": int(Config.MOBI_CASH_CASHDESKID),
        "lng": "en",
        "summa": float(amount),
        "confirm": confirm,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, json=j, headers=headers) as response:
                data = await response.json()
                return data

    except Exception as e:
        log.error(f"Error in {__name__}.deposit: {e}")
        return False


async def withdraw(user_id: int, code: str):
    step1 = sha256(f"hash={Config.MOBI_CASH_HASH_VALUE}&lng=en&userid={user_id}")
    step2 = md5(
        f"code={code}&cashierpass={Config.MOBI_CASH_CASHIERPASS}&cashdeskid={Config.MOBI_CASH_CASHDESKID}"
    )
    sign = sha256(step1 + step2)
    confirm = get_confirm(user_id, Config.MOBI_CASH_HASH_VALUE)
    headers = {"sign": sign}
    url = f"https://partners.servcul.com/CashdeskBotAPI/Deposit/{user_id}/Payout"
    j = {
        "cashdeskid": int(Config.MOBI_CASH_CASHDESKID),
        "lng": "en",
        "code": code,
        "confirm": confirm,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, json=j, headers=headers) as response:
                data = await response.json()
                return data

    except Exception as e:
        log.error(f"Error in {__name__}.deposit: {e}")
        return False


async def get_balance():
    dt = datetime.now(timezone.utc).strftime("%Y.%m.%d %H:%M:%S")
    step1 = sha256(
        f"hash={Config.MOBI_CASH_HASH_VALUE}&cashdeskid={Config.MOBI_CASH_CASHDESKID}&dt={dt}"
    )
    step2 = md5(
        f"dt={dt}&cashierpass={Config.MOBI_CASH_CASHIERPASS}&cashdeskid={Config.MOBI_CASH_CASHDESKID}"
    )
    sign = sha256(step1 + step2)
    confirm = md5(f"{Config.MOBI_CASH_CASHDESKID}:{Config.MOBI_CASH_HASH_VALUE}")
    headers = {"sign": sign}
    url = f"https://partners.servcul.com/CashdeskBotAPI/Cashdesk/{Config.MOBI_CASH_CASHDESKID}/Balance"
    params = {"confirm": confirm, "dt": dt}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                data = await response.json()
                return data

    except Exception as e:
        log.error(f"Error in {__name__}.deposit: {e}")
        return False


async def search_user(user_id: int):
    step1 = sha256(
        f"hash={Config.MOBI_CASH_HASH_VALUE}&userid={user_id}&cashdeskid={Config.MOBI_CASH_CASHDESKID}"
    )
    step2 = md5(
        f"userid={user_id}&cashierpass={Config.MOBI_CASH_CASHIERPASS}&hash={Config.MOBI_CASH_HASH_VALUE}"
    )
    sign = sha256(step1 + step2)
    confirm = get_confirm(user_id, Config.MOBI_CASH_HASH_VALUE)
    headers = {"sign": sign}
    url = f"https://partners.servcul.com/CashdeskBotAPI/Users/{user_id}"
    params = {"confirm": confirm, "cashdeskid": Config.MOBI_CASH_CASHDESKID}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                data = await response.json()
                return data

    except Exception as e:
        log.error(f"Error in {__name__}.deposit: {e}")
        return False
