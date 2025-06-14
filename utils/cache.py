from telegram.ext import ContextTypes
from utils.api_calls import get_fixture_stats
from utils.constants import SPORT_API
from common.constants import TIMEZONE
from utils.api_calls_by_sport import (
    get_last_matches_by_sport,
    get_h2h_by_sport,
    get_fixture_odds_by_sport,
    get_team_standing_by_sport,
    get_team_statistics_by_sport,
    get_fixtures_by_sport,
)
from datetime import datetime, timedelta
import asyncio
import models
import logging

log = logging.getLogger(__name__)


# region Jobs


async def cache_monthly_fixtures(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE)

    for sport in SPORT_API:
        # Get fixtures for the next 30 days
        monthly_fixtures = await get_fixtures_by_sport(
            from_date=now, duration_in_days=30, sport=sport
        )

        if not monthly_fixtures:
            return
        processed_teams = set()
        with models.session_scope() as session:
            try:
                for fixture in monthly_fixtures:
                    fixture_id = fixture["fixture_id"]
                    league_id = fixture["league_id"]
                    home_id = fixture["home_id"]
                    away_id = fixture["away_id"]
                    season = fixture["season"]
                    fixture_date = datetime.fromtimestamp(fixture["date"])

                    # Check if fixture already exists in cache
                    existing = (
                        session.query(models.CachedFixture)
                        .filter_by(fixture_id=fixture_id, sport=sport)
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
                            sport=sport,
                        )
                        session.add(new_fixture)

                        # Schedule jobs for data that might not be available yet
                        context.job_queue.run_repeating(
                            callback=store_fixture_odds,
                            interval=60 * 60,
                            first=10,
                            data={
                                "fixture_id": fixture_id,
                                "sport": sport,
                            },
                            job_kwargs={
                                "id": f"odds_{fixture_id}",
                                "replace_existing": True,
                                "misfire_grace_time": None,
                            },
                        )
                        if sport == "football":
                            context.job_queue.run_once(
                                callback=store_fixture_stats,
                                when=fixture_date
                                + timedelta(hours=2),  # 1 hour after match
                                data={
                                    "fixture_id": fixture_id,
                                },
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
                                "home_id": home_id,
                                "away_id": away_id,
                                "sport": sport,
                            },
                            job_kwargs={
                                "id": f"standings_{fixture_id}",
                                "replace_existing": True,
                            },
                        )

                        # For H2H and team stats, we can try to get them immediately
                        # Cache last results for teams if we haven't already
                        for team_id in [home_id, away_id]:
                            if team_id not in processed_teams:
                                try:
                                    last_results = await get_last_matches_by_sport(
                                        team_id=team_id, sport=sport, season=season
                                    )
                                    if last_results:
                                        # Check if we already have cached results for this team
                                        existing_results = (
                                            session.query(models.CachedTeamResults)
                                            .filter_by(team_id=team_id, sport=sport)
                                            .first()
                                        )

                                        if existing_results:
                                            existing_results.data = last_results
                                            existing_results.last_updated = (
                                                datetime.now(TIMEZONE)
                                            )
                                        else:
                                            session.add(
                                                models.CachedTeamResults(
                                                    team_id=team_id,
                                                    data=last_results,
                                                    last_updated=datetime.now(TIMEZONE),
                                                    sport=sport,
                                                )
                                            )
                                        processed_teams.add(team_id)
                                except Exception as e:
                                    print(
                                        f"Failed to cache last results for team {team_id}: {e}"
                                    )

                        try:
                            h2h_data = await get_h2h_by_sport(
                                h2h=f"{home_id}-{away_id}", sport=sport
                            )
                            if h2h_data:
                                session.add(
                                    models.CachedH2H(
                                        fixture_id=fixture_id,
                                        home_id=home_id,
                                        away_id=away_id,
                                        data=h2h_data,
                                        last_updated=datetime.now(TIMEZONE),
                                        sport=sport,
                                    )
                                )
                        except Exception as e:
                            log.error(
                                f"Failed to get H2H for fixture {fixture_id}: {e}"
                            )

                        try:
                            home_stats = await get_team_statistics_by_sport(
                                team_id=home_id,
                                league_id=league_id,
                                season=season,
                                sport=sport,
                                game_id=fixture_id,
                            )
                            if home_stats:
                                session.add(
                                    models.CachedTeamStats(
                                        fixture_id=fixture_id,
                                        team_id=home_id,
                                        league_id=league_id,
                                        season=season,
                                        data=home_stats,
                                        last_updated=datetime.now(TIMEZONE),
                                        sport=sport,
                                    )
                                )
                        except Exception as e:
                            log.error(
                                f"Failed to get home team stats for fixture {fixture_id}: {e}"
                            )

                        try:
                            away_stats = await get_team_statistics_by_sport(
                                team_id=away_id,
                                league_id=league_id,
                                season=season,
                                sport=sport,
                                game_id=fixture_id,
                            )
                            if away_stats:
                                session.add(
                                    models.CachedTeamStats(
                                        fixture_id=fixture_id,
                                        team_id=away_id,
                                        league_id=league_id,
                                        season=season,
                                        data=away_stats,
                                        last_updated=datetime.now(TIMEZONE),
                                        sport=sport,
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
    sport = context.job.data["sport"]
    try:
        odds_data = await get_fixture_odds_by_sport(fixture_id=fixture_id, sport=sport)
        if odds_data:
            with models.session_scope() as session:
                try:
                    # Check if odds already exist
                    existing = (
                        session.query(models.CachedOdds)
                        .filter_by(fixture_id=fixture_id, sport=sport)
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
                                sport=sport,
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
                        session.query(models.CachedFixtureStats)
                        .filter_by(fixture_id=fixture_id)
                        .first()
                    )
                    if existing:
                        existing.data = stats_data
                        existing.last_updated = datetime.now(TIMEZONE)
                    else:
                        session.add(
                            models.CachedFixtureStats(
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
    home_id = context.job.data["home_id"]
    away_id = context.job.data["away_id"]
    sport = context.job.data["sport"]

    try:
        home_standing = await get_team_standing_by_sport(
            team_id=home_id, league_id=league_id, season=season, sport=sport
        )
        away_standing = await get_team_standing_by_sport(
            team_id=away_id, league_id=league_id, season=season, sport=sport
        )
        if home_standing and away_standing:
            with models.session_scope() as session:
                try:
                    # Check if standings already exist
                    existing_home_standing = (
                        session.query(models.CachedStandings)
                        .filter_by(
                            team_id=home_id,
                            league_id=league_id,
                            season=season,
                            sport=sport,
                        )
                        .first()
                    )
                    if existing_home_standing:
                        existing_home_standing.data = home_standing
                        existing_home_standing.last_updated = datetime.now(TIMEZONE)
                    existing_away_standing = (
                        session.query(models.CachedStandings)
                        .filter_by(
                            team_id=away_id,
                            league_id=league_id,
                            season=season,
                            sport=sport,
                        )
                        .first()
                    )
                    if existing_away_standing:
                        existing_away_standing.data = away_standing
                        existing_away_standing.last_updated = datetime.now(TIMEZONE)

                    else:
                        session.add(
                            models.CachedStandings(
                                fixture_id=fixture_id,
                                league_id=league_id,
                                team_id=away_id,
                                season=season,
                                data=away_standing,
                                last_updated=datetime.now(TIMEZONE),
                                sport=sport,
                            )
                        )
                        session.add(
                            models.CachedStandings(
                                fixture_id=fixture_id,
                                league_id=league_id,
                                team_id=home_id,
                                season=season,
                                data=home_standing,
                                last_updated=datetime.now(TIMEZONE),
                                sport=sport,
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
