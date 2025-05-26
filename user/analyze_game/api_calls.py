from common.constants import TIMEZONE_NAME
from utils.api_calls import BASE_URL, _get_request
import logging

log = logging.getLogger(__name__)


async def get_team_statistics(team_id: int, league_id: int, season: int):
    url = f"{BASE_URL}/teams/statistics"
    params = {"team": team_id, "league": league_id, "season": season}
    return await _get_request(url, params)


async def get_team_injuries(team_id: int, season: str):
    url = f"{BASE_URL}/injuries"
    params = {"team": team_id, "season": 2024}

    return await _get_request(url, params)


async def get_team_standing(team_id: int, league_id: int, season: str):
    url = f"{BASE_URL}/standings"
    params = {"league": league_id, "season": season, "team": team_id}

    data = await _get_request(url, params)
    return data[0]["league"]["standings"][0] if data else []


async def get_last_matches(team_id: int):
    url = f"{BASE_URL}/fixtures"
    params = {"team": team_id, "last": 5}
    return await _get_request(url, params)


async def get_fixture_odds(fixture_id: int):
    url = f"{BASE_URL}/odds"
    params = {"fixture": fixture_id}
    return await _get_request(url, params)


async def get_team(name: str):
    url = f"{BASE_URL}/teams"
    querystring = {"search": name}

    return await _get_request(url, querystring)


async def search_team_id_by_name(name: str):
    url = f"{BASE_URL}/teams"
    params = {"search": name}

    return await _get_request(url, params)


async def get_h2h(h2h: str):
    url = f"{BASE_URL}/fixtures/headtohead"
    querystring = {
        "h2h": h2h,
        "timezone": TIMEZONE_NAME,
    }

    data = await _get_request(url, querystring)

    returned_fixtures = {
        "new": [],
        "finished": [],
    }

    if not data:
        return returned_fixtures

    next_fixtures = [fix for fix in data if fix["fixture"]["status"]["short"] == "NS"]
    finished_fixtures = [
        fix for fix in data if fix["fixture"]["status"]["short"] == "FT"
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
