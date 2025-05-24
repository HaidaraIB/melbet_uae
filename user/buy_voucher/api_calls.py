from utils.api_calls import HEADERS, BASE_URL
from common.constants import TIMEZONE_NAME
from datetime import datetime
import aiohttp
import asyncio
from typing import List, Dict, Any
from user.buy_voucher.constants import LEAGUE_MAP


async def get_fixtures(
    from_date: datetime,
    to_date: datetime,
    team_id: int = None,
    league_id: int = None,
) -> List[Dict[str, Any]]:
    MAX_CONCURRENT_REQUESTS = 10
    results = []
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession() as session:
        if not league_id:
            tasks = []
            for l_id in set(LEAGUE_MAP.values()):
                for season in (from_date.year, from_date.year - 1):
                    url = f"{BASE_URL}/fixtures"
                    params = {
                        "from": from_date.strftime("%Y-%m-%d"),
                        "to": to_date.strftime("%Y-%m-%d"),
                        "season": season,
                        "timezone": TIMEZONE_NAME,
                        "league": l_id,
                    }
                    if team_id:
                        params["team"] = team_id
                    tasks.append(
                        fetch_fixtures_with_rate_limit(session, url, params, semaphore)
                    )

            # Process tasks in batches with delay
            for i in range(0, len(tasks), MAX_CONCURRENT_REQUESTS):
                batch = tasks[i : i + MAX_CONCURRENT_REQUESTS]
                responses = await asyncio.gather(*batch)
                for data in responses:
                    if isinstance(data, dict) and data.get("response", []):
                        results.extend(data["response"])
                if len(results) >= 10:
                    return results
            return results
        else:
            # For single league case, we don't need rate limiting
            for season in (from_date.year, from_date.year - 1):
                url = f"{BASE_URL}/fixtures"
                params = {
                    "from": from_date.strftime("%Y-%m-%d"),
                    "to": to_date.strftime("%Y-%m-%d"),
                    "season": season,
                    "timezone": TIMEZONE_NAME,
                    "league": league_id,
                }
                if team_id:
                    params["team"] = team_id
                data = await fetch_fixtures(session, url, params)
                if data.get("response", []):
                    return data["response"]
            return []


async def fetch_fixtures_with_rate_limit(
    session: aiohttp.ClientSession,
    url: str,
    params: Dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> Dict[str, Any]:
    async with semaphore:
        return await fetch_fixtures(session, url, params)


async def fetch_fixtures(
    session: aiohttp.ClientSession,
    url: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    async with session.get(url, params=params, headers=HEADERS) as response:
        if response.status == 429:
            # Handle rate limit error
            retry_after = int(response.headers.get("Retry-After", 5))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            await asyncio.sleep(retry_after)
            return await fetch_fixtures(session, url, params)
        response.raise_for_status()
        return await response.json()


async def get_fixture_odds(fixture_id: int) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/odds", params={"fixture": fixture_id}, headers=HEADERS
        ) as response:
            data = await response.json()
            return data.get("response", [])


async def get_fixture_stats(fixture_id: int) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/fixtures/statistics",
            params={"fixture": fixture_id},
            headers=HEADERS,
        ) as response:
            data = await response.json()
            return data.get("response", [])


async def get_team_stats(team_id: int, league_id: int, season: int) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/teams/statistics",
            params={"league": league_id, "team": team_id, "season": season},
            headers=HEADERS,
        ) as response:
            data = await response.json()
            return data.get("response", {})


async def get_standings(league_id: int, season: int) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/standings",
            params={"league": league_id, "season": season},
            headers=HEADERS,
        ) as response:
            data = await response.json()
            return (
                data["response"][0]["league"]["standings"][0]
                if data.get("response")
                else []
            )


async def get_h2h(home_id: int, away_id: int) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/fixtures/headtohead",
            params={"h2h": f"{home_id}-{away_id}"},
            headers=HEADERS,
        ) as response:
            data = await response.json()
            return data.get("response", [])


async def get_last_results(team_id: int, limit: int = 5) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/fixtures",
            params={"team": team_id, "last": limit},
            headers=HEADERS,
        ) as response:
            data = await response.json()
            return data.get("response", [])
