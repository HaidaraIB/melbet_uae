from telegram.ext import ContextTypes
from utils.api_calls import BASE_URL, _get_request
from utils.constants import SPORT_API
from common.constants import TIMEZONE_NAME, TIMEZONE
from user.analyze_game.api_calls import structure_fixtures
from Config import Config
from datetime import datetime, timedelta
import asyncio
import models
from typing import List, Dict, Any
import logging

log = logging.getLogger(__name__)


async def get_fixtures(
    from_date: datetime,
    duration_in_days: int,
    sport: str,
) -> List[Dict[str, Any]]:

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


async def get_fixture_odds(fixture_id: int) -> list:
    url = f"{BASE_URL}/odds"
    params = {"fixture": fixture_id}
    return await _get_request(url, params)


async def get_fixture_stats(fixture_id: int) -> list:
    url = f"{BASE_URL}/fixtures/statistics"
    params = {"fixture": fixture_id}
    return await _get_request(url, params)


async def get_team_stats(team_id: int, league_id: int, season: int) -> dict:
    url = f"{BASE_URL}/teams/statistics"
    params = {"league": league_id, "team": team_id, "season": season}
    return await _get_request(url, params)


async def get_standings(league_id: int, season: int) -> list:
    url = f"{BASE_URL}/standings"
    params = {"league": league_id, "season": season}
    data = await _get_request(url, params)
    return data[0]["league"]["standings"][0] if data else []


async def get_h2h(home_id: int, away_id: int) -> list:
    url = f"{BASE_URL}/fixtures/headtohead"
    params = {"h2h": f"{home_id}-{away_id}"}
    return await _get_request(url, params)


async def get_last_results(team_id: int, limit: int = 5) -> list:
    url = f"{BASE_URL}/fixtures"
    params = {"team": team_id, "last": limit}
    return await _get_request(url, params)


# region Jobs


async def cache_monthly_fixtures(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE)

    # Get fixtures for the next 30 days
    monthly_fixtures = await get_fixtures(
        from_date=now, to_date=now + timedelta(days=30)
    )

    if not monthly_fixtures:
        return
    processed_teams = set()
    with models.session_scope() as session:
        try:
            for fixture in monthly_fixtures:
                fixture_id = fixture["fixture"]["id"]
                league_id = fixture["league"]["id"]
                season = fixture["league"]["season"]
                fixture_date = datetime.fromtimestamp(fixture["fixture"]["timestamp"])

                # Check if fixture already exists in cache
                existing = (
                    session.query(models.CachedFixture)
                    .filter_by(fixture_id=fixture_id)
                    .first()
                )

                if not existing:
                    # Store basic fixture data
                    new_fixture = models.CachedFixture(
                        fixture_id=fixture_id,
                        league_id=league_id,
                        season=season,
                        fixture_date=fixture_date,
                        data=fixture,
                    )
                    session.add(new_fixture)

                    # Schedule jobs for data that might not be available yet
                    context.job_queue.run_repeating(
                        callback=store_fixture_odds,
                        interval=60 * 60,
                        first=10,
                        data={"fixture_id": fixture_id},
                        job_kwargs={
                            "id": f"odds_{fixture_id}",
                            "replace_existing": True,
                            "misfire_grace_time": None,
                        },
                    )

                    context.job_queue.run_once(
                        callback=store_fixture_stats,
                        when=fixture_date + timedelta(hours=2),  # 1 hour after match
                        data={"fixture_id": fixture_id},
                        job_kwargs={
                            "id": f"stats_{fixture_id}",
                            "replace_existing": True,
                            "misfire_grace_time": None,
                        },
                    )

                    context.job_queue.run_once(
                        callback=store_standings,
                        when=fixture_date
                        - timedelta(minutes=50),  # 1 hour before match
                        data={
                            "league_id": league_id,
                            "season": season,
                            "fixture_id": fixture_id,
                        },
                        job_kwargs={
                            "id": f"standings_{fixture_id}",
                            "replace_existing": True,
                        },
                    )

                    # For H2H and team stats, we can try to get them immediately
                    home_id = fixture["teams"]["home"]["id"]
                    away_id = fixture["teams"]["away"]["id"]

                    # Cache last results for teams if we haven't already
                    for team_id in [home_id, away_id]:
                        if team_id not in processed_teams:
                            try:
                                last_results = await get_last_results(team_id)
                                if last_results:
                                    # Check if we already have cached results for this team
                                    existing_results = (
                                        session.query(models.CachedTeamResults)
                                        .filter_by(team_id=team_id)
                                        .first()
                                    )

                                    if existing_results:
                                        existing_results.data = last_results
                                        existing_results.last_updated = datetime.now(
                                            TIMEZONE
                                        )
                                    else:
                                        session.add(
                                            models.CachedTeamResults(
                                                team_id=team_id,
                                                data=last_results,
                                                last_updated=datetime.now(TIMEZONE),
                                            )
                                        )
                                    processed_teams.add(team_id)
                            except Exception as e:
                                print(
                                    f"Failed to cache last results for team {team_id}: {e}"
                                )

                    try:
                        h2h_data = await get_h2h(home_id, away_id)
                        if h2h_data:
                            session.add(
                                models.CachedH2H(
                                    fixture_id=fixture_id,
                                    home_id=home_id,
                                    away_id=away_id,
                                    data=h2h_data,
                                    last_updated=datetime.now(TIMEZONE),
                                )
                            )
                    except Exception as e:
                        log.error(f"Failed to get H2H for fixture {fixture_id}: {e}")

                    try:
                        home_stats = await get_team_stats(home_id, league_id, season)
                        if home_stats:
                            session.add(
                                models.CachedTeamStats(
                                    fixture_id=fixture_id,
                                    team_id=home_id,
                                    league_id=league_id,
                                    season=season,
                                    data=home_stats,
                                    last_updated=datetime.now(TIMEZONE),
                                )
                            )
                    except Exception as e:
                        log.error(
                            f"Failed to get home team stats for fixture {fixture_id}: {e}"
                        )

                    try:
                        away_stats = await get_team_stats(away_id, league_id, season)
                        if away_stats:
                            session.add(
                                models.CachedTeamStats(
                                    fixture_id=fixture_id,
                                    team_id=away_id,
                                    league_id=league_id,
                                    season=season,
                                    data=away_stats,
                                    last_updated=datetime.now(TIMEZONE),
                                )
                            )
                    except Exception as e:
                        log.error(
                            f"Failed to get away team stats for fixture {fixture_id}: {e}"
                        )

                session.commit()
                await asyncio.sleep(5)

        except Exception as e:
            session.rollback()
            log.error(f"Error caching monthly fixtures: {e}")


async def store_fixture_odds(context: ContextTypes.DEFAULT_TYPE):
    fixture_id = context.job.data["fixture_id"]

    try:
        odds_data = await get_fixture_odds(fixture_id)
        if odds_data:
            with models.session_scope() as session:
                try:
                    # Check if odds already exist
                    existing = (
                        session.query(models.CachedOdds)
                        .filter_by(fixture_id=fixture_id)
                        .first()
                    )
                    if existing:
                        existing.data = odds_data
                        existing.last_updated = datetime.now(TIMEZONE)
                    else:
                        session.add(
                            models.CachedOdds(
                                fixture_id=fixture_id,
                                data=odds_data,
                                last_updated=datetime.now(TIMEZONE),
                            )
                        )
                    session.commit()
                except Exception as e:
                    session.rollback()
                    log.error(f"Error storing odds for fixture {fixture_id}: {e}")
    except Exception as e:
        log.error(f"Failed to get odds for fixture {fixture_id}: {e}")


async def store_fixture_stats(context: ContextTypes.DEFAULT_TYPE):
    fixture_id = context.job.data["fixture_id"]

    try:
        stats_data = await get_fixture_stats(fixture_id)
        if stats_data:
            with models.session_scope() as session:
                try:
                    # Check if stats already exist
                    existing = (
                        session.query(models.CachedStats)
                        .filter_by(fixture_id=fixture_id)
                        .first()
                    )
                    if existing:
                        existing.data = stats_data
                        existing.last_updated = datetime.now(TIMEZONE)
                    else:
                        session.add(
                            models.CachedStats(
                                fixture_id=fixture_id,
                                data=stats_data,
                                last_updated=datetime.now(TIMEZONE),
                            )
                        )
                    session.commit()
                except Exception as e:
                    session.rollback()
                    log.error(f"Error storing stats for fixture {fixture_id}: {e}")
    except Exception as e:
        log.error(f"Failed to get stats for fixture {fixture_id}: {e}")


async def store_standings(context: ContextTypes.DEFAULT_TYPE):
    league_id = context.job.data["league_id"]
    season = context.job.data["season"]
    fixture_id = context.job.data["fixture_id"]

    try:
        standings_data = await get_standings(league_id, season)
        if standings_data:
            with models.session_scope() as session:

                try:
                    # Check if standings already exist
                    existing = (
                        session.query(models.CachedStandings)
                        .filter_by(league_id=league_id, season=season)
                        .first()
                    )

                    if existing:
                        existing.data = standings_data
                        existing.last_updated = datetime.now(TIMEZONE)
                    else:
                        session.add(
                            models.CachedStandings(
                                fixture_id=fixture_id,
                                league_id=league_id,
                                season=season,
                                data=standings_data,
                                last_updated=datetime.now(TIMEZONE),
                            )
                        )
                    session.commit()
                except Exception as e:
                    session.rollback()
                    log.error(
                        f"Error storing standings for league {league_id} season {season}: {e}"
                    )
    except Exception as e:
        log.error(
            f"Failed to get standings for league {league_id} season {season}: {e}"
        )


async def update_team_results(context: ContextTypes.DEFAULT_TYPE):
    """Periodic job to update team results for active teams"""
    with models.session_scope() as session:
        try:
            # Get all unique team IDs from upcoming fixtures
            team_ids = [
                id
                for id, in session.query(
                    models.CachedFixture.data["teams"]["home"]["id"]
                )
                .distinct()
                .all()
            ]
            team_ids += [
                id
                for id, in session.query(
                    models.CachedFixture.data["teams"]["away"]["id"]
                )
                .distinct()
                .all()
            ]
            team_ids = list(set(team_ids))

            for team_id in team_ids:
                try:
                    last_results = await get_last_results(team_id)
                    if last_results:
                        existing = (
                            session.query(models.CachedTeamResults)
                            .filter_by(team_id=team_id)
                            .first()
                        )
                        if existing:
                            existing.data = last_results
                            existing.last_updated = datetime.now(TIMEZONE)
                        else:
                            session.add(
                                models.CachedTeamResults(
                                    team_id=team_id,
                                    data=last_results,
                                    last_updated=datetime.now(TIMEZONE),
                                )
                            )
                except Exception as e:
                    print(f"Failed to update results for team {team_id}: {e}")

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error updating team results: {e}")
