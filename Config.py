import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    SESSION = os.getenv("SESSION")
    BOT_SESSION = os.getenv("BOT_SESSION")
    OWNER_ID = int(os.getenv("OWNER_ID"))
    ADMIN_ID = int(os.getenv("ADMIN_ID"))
    UAE_MONITOR_GROUP_ID = int(os.getenv("UAE_MONITOR_GROUP_ID"))
    SYR_MONITOR_GROUP_ID = int(os.getenv("SYR_MONITOR_GROUP_ID"))
    ACCOUNTS_GROUP_ID = int(os.getenv("ACCOUNTS_GROUP_ID"))
    RECEIPTS_GROUP_ID = int(os.getenv("RECEIPTS_GROUP_ID"))
    PAYLINK_BOT_ID = int(os.getenv("PAYLINK_BOT_ID"))
    PHONE = os.getenv("PHONE")
    ERRORS_CHANNEL = int(os.getenv("ERRORS_CHANNEL"))

    DB_PATH = os.getenv("DB_PATH")
    DB_POOL_SIZE = 20
    DB_MAX_OVERFLOW = 10

    GPT_MODEL = os.getenv("GPT_MODEL")
    DALL_E_MODEL = os.getenv("DALL_E_MODEL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    X_RAPIDAPI_KEY = os.getenv("X_RAPIDAPI_KEY")

    X_RAPIDAPI_FB_HOST = os.getenv("X_RAPIDAPI_FB_HOST")
    X_RAPIDAPI_BB_HOST = os.getenv("X_RAPIDAPI_BB_HOST")
    X_RAPIDAPI_AFB_HOST = os.getenv("X_RAPIDAPI_AFB_HOST")
    X_RAPIDAPI_H_HOST = os.getenv("X_RAPIDAPI_H_HOST")

    WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY")
    WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN")

    MOBI_CASH_CASHDESKID_UAE = os.getenv("MOBI_CASH_CASHDESKID_UAE")
    MOBI_CASH_CASHIERPASS_UAE = os.getenv("MOBI_CASH_CASHIERPASS_UAE")
    MOBI_CASH_HASH_VALUE_UAE = os.getenv("MOBI_CASH_HASH_VALUE_UAE")

    MOBI_CASH_CASHDESKID_SYR = os.getenv("MOBI_CASH_CASHDESKID_SYR")
    MOBI_CASH_CASHIERPASS_SYR = os.getenv("MOBI_CASH_CASHIERPASS_SYR")
    MOBI_CASH_HASH_VALUE_SYR = os.getenv("MOBI_CASH_HASH_VALUE_SYR")

    STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
