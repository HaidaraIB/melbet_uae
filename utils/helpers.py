import aiohttp
from Config import Config
import logging
import asyncio

log = logging.getLogger(__name__)


BASE_URL = f"https://{Config.X_RAPIDAPI_FB_HOST}/v3"
HEADERS = {
    "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
    "X-RapidAPI-Host": Config.X_RAPIDAPI_FB_HOST,
}


async def handle_rate_limit(func, *args):
    # Handle rate limit error
    log.warning(f"Rate limited. Waiting 5 seconds...")
    await asyncio.sleep(5)
    return await func(*args)


async def _get_request(url, params, headers=HEADERS):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 429:
                    return await handle_rate_limit(_get_request, url, params, headers)
                data = await response.json()
                return data.get("response", [])

    except Exception as e:
        log.error(f"Error in _get_request: {e}")
        return []
