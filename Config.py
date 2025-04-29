import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    SESSION = os.getenv("SESSION")
    OWNER_ID = int(os.getenv("OWNER_ID"))
    ERRORS_CHANNEL = int(os.getenv("ERRORS_CHANNEL"))
    FORCE_JOIN_CHANNEL_ID = int(os.getenv("FORCE_JOIN_CHANNEL_ID"))
    FORCE_JOIN_CHANNEL_LINK = os.getenv("FORCE_JOIN_CHANNEL_LINK")

    DB_PATH = os.getenv("DB_PATH")
    DB_POOL_SIZE = 20
    DB_MAX_OVERFLOW = 10
