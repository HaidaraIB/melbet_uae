from common.constants import TIMEZONE_NAME, TIMEZONE
from utils.constants import SPORT_API
from utils.api_calls import _get_request
from utils.functions import structure_fixtures
import logging
from datetime import datetime, timedelta
from Config import Config

log = logging.getLogger(__name__)


async def search_team_id_by_name(name: str, sport: str):
    spec = SPORT_API.get(sport)
    url = f"https://{spec['host']}/teams"
    if sport == "football":
        url = f"https://{spec['host']}/v3/teams"
    headers = {
        "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": spec["host"],
    }
    params = {"name": name}

    return await _get_request(url=url, params=params, headers=headers)


async def get_team_statistics_by_sport(
    team_id: int,
    league_id: int,
    season: int,
    sport: str,
    game_id: int,
):
    spec = SPORT_API.get(sport)
    if not spec["team_statistics_url"]:
        return []
    headers = {
        "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": spec["host"],
    }
    params = {
        "team": team_id,
        "league": league_id,
        "season": season,
    }
    if sport == "american_football":
        params = {
            "id": game_id,
            "team": team_id,
        }
    return await _get_request(
        url=spec["team_statistics_url"], params=params, headers=headers
    )


async def get_team_injuries_by_sport(team_id: int, season: str, sport: str):
    spec = SPORT_API.get(sport)
    if not spec["team_injuries_url"]:
        return []
    headers = {
        "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": spec["host"],
    }
    params = {"team": team_id, "season": season}

    return await _get_request(
        url=spec["team_injuries_url"], params=params, headers=headers
    )


async def get_team_standing_by_sport(
    team_id: int, league_id: int, season: str, sport: str
):
    spec = SPORT_API.get(sport)
    url = f"https://{spec['host']}/standings"
    if sport == "football":
        url = f"https://{spec['host']}/v3/standings"

    headers = {
        "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": spec["host"],
    }
    params = {"league": league_id, "season": season, "team": team_id}

    return await _get_request(url=url, params=params, headers=headers)


async def get_fixture_odds_by_sport(fixture_id: int, sport: str):
    spec = SPORT_API.get(sport)
    url = f"https://{spec['host']}/odds"
    if sport == "football":
        url = f"https://{spec['host']}/v3/odds"
    headers = {
        "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": spec["host"],
    }
    params = {"game": fixture_id}
    if sport == "football":
        params = {"fixture": fixture_id}
    return await _get_request(url=url, params=params, headers=headers)


async def get_last_matches_by_sport(team_id: int, sport: str, season: str | int):
    spec = SPORT_API.get(sport)
    headers = {
        "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": spec["host"],
    }
    url = f"https://{spec['host']}/games"
    params = {"team": team_id, "season": season}
    if sport == "football":
        url = f"https://{spec['host']}/v3/fixtures"
        params = {"team": team_id, "last": 5}
    return await _get_request(url=url, params=params, headers=headers)


async def get_fixtures_by_sport(
    from_date: datetime,
    duration_in_days: int,
    sport: str,
):

    spec = SPORT_API.get(sport)
    if not spec:
        return []

    headers = {
        "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": spec["host"],
    }
    data = []
    for day in range(duration_in_days):
        params = {
            "date": (from_date + timedelta(days=day)).strftime("%Y-%m-%d"),
            "timezone": TIMEZONE_NAME,
        }
        data += await _get_request(
            url=spec["fixtures_url"], params=params, headers=headers
        )
    if not data:
        return []

    fixtures = structure_fixtures(sport=sport, data=data)

    return fixtures


async def get_h2h_by_sport(h2h: str, sport: str):
    spec = SPORT_API.get(sport)
    if not spec:
        return []

    headers = {
        "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": spec["host"],
    }
    params = {
        "h2h": h2h,
        "timezone": TIMEZONE_NAME,
    }

    data = await _get_request(url=spec["h2h_url"], params=params, headers=headers)
    fixtures = []

    if not data:
        return fixtures

    data = list(reversed(data))

    fixtures = structure_fixtures(sport=sport, data=data, fix_num=6)

    return fixtures
