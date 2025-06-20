from telegram.ext import ContextTypes
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
from utils.api_calls import get_fixture_stats
from datetime import datetime, timedelta
import asyncio
import models
import logging

log = logging.getLogger(__name__)


# region Jobs


async def cache_monthly_fixtures(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE)

    for sport in SPORT_API:
        monthly_fixtures = await get_fixtures_by_sport(
            from_date=now, duration_in_days=30, sport=sport
        )

        if not monthly_fixtures:
            return
        processed_teams = set()
        with models.session_scope() as session:
            for fixture in monthly_fixtures:
                fixture_id = fixture["fixture_id"]
                league_id = fixture["league_id"]
                home_id = fixture["home_id"]
                away_id = fixture["away_id"]
                season = fixture["season"]
                fixture_date = datetime.fromtimestamp(fixture["date"])

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
                        when=fixture_date + timedelta(hours=2),  # 1 hour after match
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
                    when=fixture_date - timedelta(minutes=50),  # 1 hour before match
                    data={
                        "league_id": league_id,
                        "season": season,
                        "home_id": home_id,
                        "away_id": away_id,
                        "sport": sport,
                    },
                    job_kwargs={
                        "id": f"standings_{fixture_id}",
                        "replace_existing": True,
                    },
                )

                for team_id in [home_id, away_id]:
                    if team_id not in processed_teams:
                        await get_last_matches_by_sport(
                            team_id=team_id, sport=sport, season=season
                        )

                await get_h2h_by_sport(h2h=f"{home_id}-{away_id}", sport=sport)

                await get_team_statistics_by_sport(
                    team_id=home_id,
                    league_id=league_id,
                    season=season,
                    sport=sport,
                    game_id=fixture_id,
                )

                await get_team_statistics_by_sport(
                    team_id=away_id,
                    league_id=league_id,
                    season=season,
                    sport=sport,
                    game_id=fixture_id,
                )

                session.commit()
                await asyncio.sleep(5)


async def store_fixture_odds(context: ContextTypes.DEFAULT_TYPE):
    fixture_id = context.job.data["fixture_id"]
    sport = context.job.data["sport"]
    await get_fixture_odds_by_sport(fixture_id=fixture_id, sport=sport)


async def store_fixture_stats(context: ContextTypes.DEFAULT_TYPE):
    fixture_id = context.job.data["fixture_id"]
    await get_fixture_stats(fixture_id=fixture_id)


async def store_standings(context: ContextTypes.DEFAULT_TYPE):
    league_id = context.job.data["league_id"]
    season = context.job.data["season"]
    home_id = context.job.data["home_id"]
    away_id = context.job.data["away_id"]
    sport = context.job.data["sport"]

    await get_team_standing_by_sport(
        team_id=home_id, league_id=league_id, season=season, sport=sport
    )
    await get_team_standing_by_sport(
        team_id=away_id, league_id=league_id, season=season, sport=sport
    )
