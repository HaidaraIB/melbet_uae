import aiohttp
from Config import Config
import logging

log = logging.getLogger(__name__)


async def check_reg_account(tg_id: int):
    url = f"https://webhook.site/token/{Config.WEBHOOK_TOKEN}/requests"
    headers = {"Api-Key": Config.WEBHOOK_API_KEY}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    for req in data["data"]:
                        if (
                            req["query"]
                            and req["query"].get("tg_id", None) == str(tg_id)
                            and req["query"].get("reg", None)
                            and not req['user_agent']
                        ):
                            return True
        return False
    except Exception as e:
        log.error(f"Exception: {e}")
        return False
