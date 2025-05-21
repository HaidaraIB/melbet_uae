import aiohttp
import asyncio
from common.constants import TIMEZONE_NAME
from utils.api_calls import HEADERS, BASE_URL
import logging

log = logging.getLogger(__name__)


async def get_team_statistics(team_id: int, league_id: int, season: int):
    url = f"{BASE_URL}/teams/statistics"
    params = {"team": team_id, "league": league_id, "season": season}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=HEADERS) as response:
            data = await response.json()
            return data.get("response", [])


async def get_team_injuries(team_id: int, season: str):
    url = f"{BASE_URL}/injuries"
    params = {"team": team_id, "season": 2024}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=HEADERS) as response:
            data = await response.json()
            return data.get("response", [])


async def get_team_standing(team_id: int, league_id: int, season: str):
    url = f"{BASE_URL}/standings"
    params = {"league": league_id, "season": season, "team": team_id}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=HEADERS) as response:
            data = await response.json()
            if data.get("response", None):
                return data['response'][0]["league"]["standings"][0]
            return []


async def get_last_matches(team_id: int):
    url = f"{BASE_URL}/fixtures"
    params = {"team": team_id, "last": 5}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=HEADERS) as response:
            data = await response.json()
            return data.get("response", [])


async def get_fixture_odds(fixture_id: int):
    url = f"{BASE_URL}/odds"
    params = {"fixture": fixture_id}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=HEADERS) as response:
            data = await response.json()
            return data.get("response", [])


async def get_team(name: str):
    url = f"{BASE_URL}/teams"
    querystring = {"search": name}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=querystring, headers=HEADERS) as response:
            data = await response.json()
            return data.get("response", [])


async def search_team_id_by_name(name: str):
    url = f"{BASE_URL}/teams"
    params = {"search": name}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=HEADERS) as response:
            data = await response.json()
            return data.get("response", [])


async def get_h2h(h2h: str):
    url = f"{BASE_URL}/fixtures/headtohead"
    querystring = {
        "h2h": h2h,
        "timezone": TIMEZONE_NAME,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=querystring, headers=HEADERS) as response:
            data = await response.json()

    returned_fixtures = {
        "new": [],
        "finished": [],
    }

    if not data.get("response"):
        return returned_fixtures

    next_fixtures = [
        fix for fix in data["response"] if fix["fixture"]["status"]["short"] == "NS"
    ]
    finished_fixtures = [
        fix for fix in data["response"] if fix["fixture"]["status"]["short"] == "FT"
    ]
    for fixture in next_fixtures:
        returned_fixtures["new"].append(
            {
                "teams": fixture["teams"],
                "goals": fixture["goals"],
                "fixture": fixture["fixture"],
                "league": fixture["league"],
            }
        )
    for fixture in finished_fixtures:
        returned_fixtures["finished"].append(
            {
                "teams": fixture["teams"],
                "goals": fixture["goals"],
                "fixture": fixture["fixture"],
                "league": fixture["league"],
            }
        )
        if len(returned_fixtures["finished"]) == 5:
            break
    return returned_fixtures
