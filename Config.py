import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    SESSION = os.getenv("SESSION")
    OWNER_ID = int(os.getenv("OWNER_ID"))
    ADMIN_ID = int(os.getenv("ADMIN_ID"))
    MONITOR_GROUP_ID = int(os.getenv("MONITOR_GROUP_ID"))
    PHONE = os.getenv("PHONE")
    ERRORS_CHANNEL = int(os.getenv("ERRORS_CHANNEL"))
    FORCE_JOIN_CHANNEL_ID = int(os.getenv("FORCE_JOIN_CHANNEL_ID"))
    FORCE_JOIN_CHANNEL_LINK = os.getenv("FORCE_JOIN_CHANNEL_LINK")

    DB_PATH = os.getenv("DB_PATH")
    DB_POOL_SIZE = 20
    DB_MAX_OVERFLOW = 10

    GPT_MODEL = os.getenv("GPT_MODEL")
    DALL_E_MODEL = os.getenv("DALL_E_MODEL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    X_RAPIDAPI_KEY = os.getenv("X_RAPIDAPI_KEY")
    X_RAPIDAPI_HOST = os.getenv("X_RAPIDAPI_HOST")
