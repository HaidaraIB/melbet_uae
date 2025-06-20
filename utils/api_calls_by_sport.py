from common.constants import TIMEZONE_NAME
from utils.constants import SPORT_API
from utils.helpers import _get_request
from utils.functions import structure_fixtures
import logging
from datetime import datetime, timedelta
from Config import Config
import models

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

    response = await _get_request(url=url, params=params, headers=headers)
    if response:
        with models.session_scope() as s:
            existing_teams = s.query(models.CachedTeams).filter_by(name=name).first()
            if not existing_teams:
                s.add(
                    models.CachedTeams(
                        name=name,
                        data=response,
                        sport=sport,
                        last_updated=datetime.now(),
                    )
                )
            else:
                existing_teams.data = response
                existing_teams.last_updated = datetime.now()
            s.commit()
    return response


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
    response = await _get_request(
        url=spec["team_statistics_url"], params=params, headers=headers
    )
    if response:
        with models.session_scope() as s:
            existing_team_stats = (
                s.query(models.CachedTeamStats)
                .filter_by(
                    team_id=team_id,
                    league_id=league_id,
                    season=season,
                    sport=sport,
                )
                .first()
            )
            if not existing_team_stats:
                if game_id:
                    existing_team_stats = (
                        s.query(models.CachedTeamStats)
                        .filter_by(
                            team_id=team_id,
                            game_id=game_id,
                            sport=sport,
                        )
                        .first()
                    )
                    if not existing_team_stats:
                        s.add(
                            models.CachedTeamStats(
                                team_id=team_id,
                                league_id=league_id,
                                season=season,
                                data=response,
                                last_updated=datetime.now(),
                                sport=sport,
                                game_id=game_id,
                            )
                        )
                    else:
                        existing_team_stats.data = response
                        existing_team_stats.last_updated = datetime.now()
                else:
                    s.add(
                        models.CachedTeamStats(
                            team_id=team_id,
                            league_id=league_id,
                            season=season,
                            data=response,
                            last_updated=datetime.now(),
                            sport=sport,
                        )
                    )
            else:
                existing_team_stats.data = response
                existing_team_stats.last_updated = datetime.now()
            s.commit()
    return response


async def get_team_injuries_by_sport(team_id: int, season: str, sport: str):
    spec = SPORT_API.get(sport)
    if not spec["team_injuries_url"]:
        return []
    headers = {
        "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": spec["host"],
    }
    params = {"team": team_id, "season": season}

    response = await _get_request(
        url=spec["team_injuries_url"], params=params, headers=headers
    )
    if response:
        with models.session_scope() as s:
            existing_injuries = (
                s.query(models.CachedInjuries)
                .filter_by(team_id=team_id, season=season, sport=sport)
                .first()
            )
            if not existing_injuries:
                s.add(
                    models.CachedInjuries(
                        team_id=team_id,
                        season=season,
                        data=response,
                        last_updated=datetime.now(),
                        sport=sport,
                    )
                )
            else:
                existing_injuries.data = response
                existing_injuries.last_updated = datetime.now()
            s.commit()
    return response


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

    response = await _get_request(url=url, params=params, headers=headers)
    if response:
        with models.session_scope() as s:
            existing_standings = (
                s.query(models.CachedStandings)
                .filter_by(
                    team_id=team_id,
                    league_id=league_id,
                    season=season,
                    sport=sport,
                )
                .first()
            )
            if not existing_standings:
                s.add(
                    models.CachedStandings(
                        league_id=league_id,
                        team_id=team_id,
                        season=season,
                        data=response,
                        last_updated=datetime.now(),
                        sport=sport,
                    )
                )
            else:
                existing_standings.data = response
                existing_standings.last_updated = datetime.now()
            s.commit()
    return response


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
    response = await _get_request(url=url, params=params, headers=headers)
    if response:
        with models.session_scope() as s:
            existing_odds = (
                s.query(models.CachedOdds)
                .filter_by(fixture_id=fixture_id, sport=sport)
                .first()
            )
            if not existing_odds:
                cached_fixture = (
                    s.query(models.CachedFixture)
                    .filter_by(fixture_id=fixture_id, sport=sport)
                    .first()
                )
                # TODO if it's not there, get and cache it.
                s.add(
                    models.CachedOdds(
                        cached_fixture_id=cached_fixture.id,
                        data=response,
                        last_updated=datetime.now(),
                        sport=sport,
                    )
                )
            else:
                existing_odds.data = response
                existing_odds.last_updated = datetime.now()
            s.commit()

    return response


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
    response = await _get_request(url=url, params=params, headers=headers)
    if response:
        with models.session_scope() as s:
            cached_team_results = (
                s.query(models.CachedTeamResults)
                .filter_by(team_id=team_id, sport=sport)
                .first()
            )
            if not cached_team_results:
                s.add(
                    models.CachedTeamResults(
                        team_id=team_id,
                        data=response,
                        last_updated=datetime.now(),
                        sport=sport,
                    )
                )
            else:
                cached_team_results.data = response
                cached_team_results.last_updated = datetime.now()
            s.commit()
    return response


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
    with models.session_scope() as s:
        for fix in fixtures:
            existing_fix = (
                s.query(models.CachedFixture)
                .filter_by(fixture_id=fix["fixture_id"], sport=sport)
                .first()
            )
            if not existing_fix:
                s.add(
                    models.CachedFixture(
                        fixture_id=fix["fixture_id"],
                        league_id=fix["league_id"],
                        season=fix["season"],
                        fixture_date=fix["date"],
                        data=fix,
                        sport=sport,
                    )
                )
                s.commit()
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
    with models.session_scope() as s:
        for fix in fixtures:
            existing_h2h = (
                s.query(models.CachedH2H)
                .filter_by(fixture_id=fix["fixture_id"], sport=sport)
                .first()
            )
            if not existing_h2h:
                s.add(
                    models.CachedH2H(
                        fixture_id=fix["fixture_id"],
                        home_id=fix["home_id"],
                        away_id=fix["away_id"],
                        data=fix,
                        last_updated=datetime.now(),
                        sport=sport,
                    )
                )
                s.commit()

    return fixtures
