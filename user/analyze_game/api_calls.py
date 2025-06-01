from common.constants import TIMEZONE_NAME, SPORT_API, TIMEZONE
from utils.api_calls import _get_request
import logging
from datetime import datetime
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
    team_id: int, league_id: int, season: int, sport: str
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
    url = f"https://{spec['host']}/fixtures"
    params = {"team": team_id, "season": season}
    if sport == "football":
        url = f"https://{spec['host']}/v3/fixtures"
        params = {"team": team_id, "last": 5}
    return await _get_request(url=url, params=params, headers=headers)


async def get_fixtures_by_sport(sport: str) -> list[dict]:
    spec = SPORT_API.get(sport)
    if not spec:
        return []

    headers = {
        "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": spec["host"],
    }
    params = {"date": datetime.now(TIMEZONE).strftime("%Y-%m-%d")}

    data = await _get_request(url=spec["fixtures_url"], params=params, headers=headers)
    if not data:
        return []
    
    fixtures = []
    if sport == "football":
        for item in data:
            fixture = item["fixture"]
            teams = item["teams"]
            fixtures.append(
                {
                    "fixture_id": fixture["id"],
                    "home_id": teams["home"]["id"],
                    "away_id": teams["away"]["id"],
                    "home_name": teams["home"]["name"],
                    "away_name": teams["away"]["name"],
                    "season": item["league"]["season"],
                    "league_id": item["league"]["id"],
                    "league_name": item["league"]["name"],
                    "venue": fixture["venue"]["name"],
                    "date": fixture["date"],
                }
            )

    elif sport == "basketball":
        for item in data:
            teams = item["teams"]
            fixtures.append(
                {
                    "fixture_id": item["id"],
                    "home_id": teams["home"]["id"],
                    "away_id": teams["away"]["id"],
                    "home_name": teams["home"]["name"],
                    "away_name": teams["away"]["name"],
                    "season": item["league"]["season"],
                    "league_id": item["league"]["id"],
                    "league_name": item["league"]["name"],
                    "venue": item["venue"],
                    "date": item["date"],
                }
            )

    elif sport == "american_football":
        for item in data:
            fixture = item["game"]
            teams = item["teams"]
            fixtures.append(
                {
                    "fixture_id": fixture["id"],
                    "home_id": teams["home"]["id"],
                    "away_id": teams["away"]["id"],
                    "home_name": teams["home"]["name"],
                    "away_name": teams["away"]["name"],
                    "season": item["league"]["season"],
                    "league_id": item["league"]["id"],
                    "league_name": item["league"]["name"],
                    "venue": fixture["venue"]["name"],
                    "date": item["date"],
                }
            )

    elif sport == "hockey":
        for item in data:
            teams = item["teams"]
            fixtures.append(
                {
                    "fixture_id": item["id"],
                    "home_id": teams["home"]["id"],
                    "away_id": teams["away"]["id"],
                    "home_name": teams["home"]["name"],
                    "away_name": teams["away"]["name"],
                    "season": item["league"]["season"],
                    "league_id": item["league"]["id"],
                    "league_name": item["league"]["name"],
                    "venue": "N/A",
                    "date": item["date"],
                }
            )

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
    returned_fixtures = []

    if not data:
        return returned_fixtures

    data = list(reversed(data))

    # ---- Football ----
    if sport == "football":
        for fix in data[:6]:
            fixture = fix["fixture"]
            teams = fix["teams"]
            item = {
                "fixture_id": fixture["id"],
                "home_id": teams["home"]["id"],
                "away_id": teams["away"]["id"],
                "home_name": teams["home"]["name"],
                "away_name": teams["away"]["name"],
                "season": fix["league"]["season"],
                "league_id": fix["league"]["id"],
                "league_name": fix["league"]["name"],
                "venue": fixture["venue"]["name"],
                "date": fixture["date"],
                "goals": fix["goals"],
            }
            returned_fixtures.append(item)

    # ---- Basketball ----
    elif sport == "basketball":
        for fix in data[:6]:
            teams = fix["teams"]
            item = {
                "fixture_id": fix["id"],
                "home_id": teams["home"]["id"],
                "away_id": teams["away"]["id"],
                "home_name": teams["home"]["name"],
                "away_name": teams["away"]["name"],
                "season": fix["league"]["season"],
                "league_id": fix["league"]["id"],
                "league_name": fix["league"]["name"],
                "venue": fix["venue"],
                "date": fix["date"],
                "goals": fix["scores"],
            }
            returned_fixtures.append(item)

    # ---- American Football ----
    elif sport == "american_football":
        for fix in data[:6]:
            teams = fix["teams"]
            fixture = fix["game"]
            item = {
                "fixture_id": fixture["id"],
                "home_id": teams["home"]["id"],
                "away_id": teams["away"]["id"],
                "home_name": teams["home"]["name"],
                "away_name": teams["away"]["name"],
                "season": fix["league"]["season"],
                "league_id": fix["league"]["id"],
                "league_name": fix["league"]["name"],
                "venue": fixture["venue"]["name"],
                "date": fix["date"],
                "goals": fix["scores"],
            }
            returned_fixtures.append(item)

    # ---- Hockey ----
    elif sport == "hockey":
        for fix in data[:6]:
            teams = fix["teams"]
            item = {
                "fixture_id": fix["id"],
                "home_id": teams["home"]["id"],
                "away_id": teams["away"]["id"],
                "home_name": teams["home"]["name"],
                "away_name": teams["away"]["name"],
                "season": fix["league"]["season"],
                "league_id": fix["league"]["id"],
                "league_name": fix["league"]["name"],
                "venue": "N/A",
                "date": fix["date"],
                "goals": fix["scores"],
            }
            returned_fixtures.append(item)

    return returned_fixtures
