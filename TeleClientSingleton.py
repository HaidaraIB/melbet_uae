from telethon import TelegramClient
from Config import Config


class TeleClientSingleton(TelegramClient):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:

            cls._instance = TelegramClient(
                session=Config.SESSION,
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
            ).start(
                phone=Config.PHONE,
            )
        return cls._instance

