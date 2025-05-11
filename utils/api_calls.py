import requests
from datetime import datetime, timedelta
from Config import Config
from telegram.ext import ContextTypes
from common.constants import TIMEZONE, TIMEZONE_NAME
import logging
import asyncio

log = logging.getLogger(__name__)


BASE_URL = f"https://{Config.X_RAPIDAPI_HOST}/v3"
HEADERS = {
    "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
    "X-RapidAPI-Host": Config.X_RAPIDAPI_HOST,
}


IMPORTANT_LEAGUES = {
    # Top 5 European Leagues
    "premier_league": {
        "name": "Premier League",
        "country": "England",
        "id": 39,
    },
    "la_liga": {
        "name": "La Liga",
        "country": "Spain",
        "id": 140,
    },
    "bundesliga": {
        "name": "Bundesliga",
        "country": "Germany",
        "id": 78,
    },
    "serie_a": {
        "name": "Serie A",
        "country": "Italy",
        "id": 135,
    },
    "ligue_1": {
        "name": "Ligue 1",
        "country": "France",
        "id": 61,
    },
    # European Competitions
    "champions_league": {
        "name": "UEFA Champions League",
        "country": "Europe",
        "id": 2,
    },
    "europa_league": {
        "name": "UEFA Europa League",
        "country": "Europe",
        "id": 3,
    },
    "europa_conference": {
        "name": "UEFA Europa Conference League",
        "country": "Europe",
        "id": 848,
    },
    # Other Major Leagues
    "mls": {
        "name": "Major League Soccer",
        "country": "USA",
        "id": 253,
    },
    "brasileirao": {
        "name": "Brasileirão Série A",
        "country": "Brazil",
        "id": 71,
    },
    "eredivisie": {
        "name": "Eredivisie",
        "country": "Netherlands",
        "id": 88,
    },
    "primeira_liga": {
        "name": "Primeira Liga",
        "country": "Portugal",
        "id": 94,
    },
    "saudi_pro": {
        "name": "Saudi Pro League",
        "country": "Saudi Arabia",
        "id": 307,
    },
    # South American Competitions
    "libertadores": {
        "name": "Copa Libertadores",
        "country": "South America",
        "id": 13,
    },
    "sudamericana": {
        "name": "Copa Sudamericana",
        "country": "South America",
        "id": 15,
    },
    # Domestic Cups
    "fa_cup": {
        "name": "FA Cup",
        "country": "England",
        "id": 45,
    },
    "efl_cup": {
        "name": "EFL Cup (Carabao Cup)",
        "country": "England",
        "id": 46,
    },
    "dfb_pokal": {
        "name": "DFB-Pokal",
        "country": "Germany",
        "id": 81,
    },
    "copa_del_rey": {
        "name": "Copa del Rey",
        "country": "Spain",
        "id": 143,
    },
    "coppa_italia": {
        "name": "Coppa Italia",
        "country": "Italy",
        "id": 137,
    },
    "coupe_de_france": {
        "name": "Coupe de France",
        "country": "France",
        "id": 66,
    },
}


def get_fixture_lineups(fixture_id: int) -> tuple:
    """Fetch starting lineups for a fixture"""
    url = f"{BASE_URL}/fixtures/lineups"
    querystring = {"fixture": fixture_id}

    try:
        response = requests.get(url, headers=HEADERS, params=querystring)
        data = response.json()

        if not data["response"]:
            return None, None

        home = data["response"][0]
        away = data["response"][1]

        def format_lineup(team):
            lineup = f"<b>{team['team']['name']} ({team['formation']})</b>\n"
            lineup += "<b>Starting XI:</b>\n"
            lineup += "\n".join(
                [
                    f"• {player['player']['name']} ({player['player']['number']})"
                    for player in team["startXI"]
                ]
            )
            lineup += "\n\n<b>Substitutes:</b>\n"
            lineup += "\n".join(
                [
                    f"• {player['player']['name']} ({player['player']['number']})"
                    for player in team["substitutes"]
                ]
            )
            return lineup

        return format_lineup(home), format_lineup(away)

    except Exception as e:
        log.error(f"Error fetching lineups: {e}")
        return None, None


def get_fixture_stats(fixture_id: int) -> dict:
    """Fetch statistics for a fixture"""
    url = f"{BASE_URL}/fixtures/statistics"
    querystring = {"fixture": fixture_id}

    try:
        response = requests.get(url, headers=HEADERS, params=querystring)
        return response.json()["response"]
    except Exception as e:
        log.error(f"Error fetching stats: {e}")
        return None


def get_fixture_events(fixture_id: int) -> list:
    """Fetch events for a fixture"""
    url = f"{BASE_URL}/fixtures/events"
    querystring = {"fixture": fixture_id}

    try:
        response = requests.get(url, headers=HEADERS, params=querystring)
        return response.json()["response"]
    except Exception as e:
        log.error(f"Error fetching events: {e}")
        return []


def build_match_stats_message_from_json(json_data: list) -> str:
    """Convert API stats data to formatted message (HTML)"""
    team1 = json_data[0]["team"]["name"]
    stats1 = {item["type"]: item["value"] for item in json_data[0]["statistics"]}
    team2 = json_data[1]["team"]["name"]
    stats2 = {item["type"]: item["value"] for item in json_data[1]["statistics"]}

    def format_stat_row(emoji: str, label: str, stat_key: str) -> str:
        val1 = stats1.get(stat_key, "N/A")
        val2 = stats2.get(stat_key, "N/A")

        return (
            f"{emoji} <b>{label}</b>\n"
            f"<code>{team1[:12]:<12} {str(val1):>5}</code>\n"
            f"<code>{team2[:12]:<12} {str(val2):>5}</code>\n"
        )

    message_lines = [
        f"⚽ <b>{team1} vs {team2}</b> ⚽",
        "",
        "📊 <b>Match Statistics</b>",
        "",
        format_stat_row("🔵", "Possession", "Ball Possession"),
        format_stat_row("🎯", "Shots on Target", "Shots on Goal"),
        format_stat_row("⚡", "Total Shots", "Total Shots"),
        format_stat_row("📦", "Shots in Box", "Shots insidebox"),
        format_stat_row("🔄", "Total Passes", "Total passes"),
        format_stat_row("🎯", "Pass Accuracy", "Passes %"),
        format_stat_row("🧤", "Goalkeeper Saves", "Goalkeeper Saves"),
        format_stat_row("↗️", "Corner Kicks", "Corner Kicks"),
        format_stat_row("🟨", "Yellow Cards", "Yellow Cards"),
        "",
        "🔹 <i>Stats update in real-time</i>",
    ]

    return "\n".join(message_lines)


async def get_daily_fixtures() -> list[dict]:
    """Fetch all fixtures for today across important leagues"""
    now = datetime.now(TIMEZONE)
    today = now.strftime("%Y-%m-%d")
    seasons = now.year - 1, now.year
    all_fixtures = []

    for league_id in [league["id"] for league in IMPORTANT_LEAGUES.values()]:
        url = f"{BASE_URL}/fixtures"
        for season in seasons:
            querystring = {
                "league": league_id,
                "date": today,
                "timezone": TIMEZONE_NAME,
                "season": season,
            }

            try:
                response = requests.get(url, headers=HEADERS, params=querystring)
                data = response.json()

                if data["response"]:
                    for fixture in data["response"]:
                        all_fixtures.append(
                            {
                                "fixture_id": fixture["fixture"]["id"],
                                "home_team": fixture["teams"]["home"]["name"],
                                "away_team": fixture["teams"]["away"]["name"],
                                "start_time": datetime.fromtimestamp(
                                    fixture["fixture"]["timestamp"], tz=TIMEZONE
                                ),
                                "league_id": league_id,
                                "league_name": next(
                                    league["name"]
                                    for league in IMPORTANT_LEAGUES.values()
                                    if league["id"] == league_id
                                ),
                            }
                        )
                await asyncio.sleep(5)
            except Exception as e:
                log.error(f"Error fetching fixtures for league {league_id}: {e}")

    return all_fixtures


def get_fixture_status(fixture_id: int) -> str:
    """Check if fixture has ended"""
    url = f"{BASE_URL}/fixtures"
    querystring = {"id": fixture_id}

    try:
        response = requests.get(url, headers=HEADERS, params=querystring)
        data = response.json()
        return data["response"][0]["fixture"]["status"]["short"]  # FT, NS, 1H, HT, etc.
    except Exception as e:
        log.error(f"Error checking fixture status: {e}")
        return "UNKNOWN"


# region Jobs


async def monitor_live_events(context: ContextTypes.DEFAULT_TYPE):
    """Enhanced monitoring with match completion detection"""
    match = context.job.data

    # First check if match has ended
    status = get_fixture_status(match["fixture_id"])
    if status == "FT":
        # Match finished, post stats and remove monitoring job
        await _send_post_match_stats(match=match, context=context)
        context.job.schedule_removal()
        return

    # Proceed with normal event monitoring if match is still ongoing
    events = get_fixture_events(match["fixture_id"])

    if not events:
        return

    last_event_id = match.get("last_event_id", 0)
    new_events = [e for e in events if e.get("id", 0) > last_event_id]

    for event in new_events:
        if event["type"].lower() in ["goal", "redcard", "penalty"]:
            emoji = {"goal": "⚽", "redcard": "🟥", "penalty": "🎯"}.get(
                event["type"].lower(), "ℹ"
            )

            message = (
                f"{emoji} <b>{event['type'].upper()}</b> {emoji}\n"
                f"<b>{event['player']['name']}</b> ({event['team']['name']})\n"
                f"⏱️ Minute: <code>{event['time']['elapsed']}'</code>"
            )

            await context.bot.send_message(
                chat_id=Config.MONITOR_GROUP_ID,
                text=message,
            )
            match["last_event_id"] = event["id"]


async def schedule_daily_fixtures(context: ContextTypes.DEFAULT_TYPE):
    # Get today's fixtures
    fixtures = await get_daily_fixtures()

    if not fixtures:
        return

    # Schedule updates for each match with lost time handling
    now = datetime.now(TIMEZONE)
    for fixture in fixtures:
        status = get_fixture_status(fixture["fixture_id"])

        match_data = {
            **fixture,
            "last_event_id": 0,
        }
        start_time: datetime = fixture["start_time"]

        # Handle matches that already started but haven't finished
        if start_time <= now <= (start_time + timedelta(hours=3)):

            if status != "FT":
                # Match is in progress, schedule immediate monitoring
                context.job_queue.run_repeating(
                    callback=monitor_live_events,
                    interval=30,
                    first=30,
                    data=match_data,
                    name=f"match_update_{fixture['fixture_id']}_monitor",
                    job_kwargs={
                        "id": f"monitor_live_events_{fixture['fixture_id']}",
                        "replace_existing": True,
                    },
                )

                # Check if we missed lineups (if match started less than 55 mins ago)
                if now < (start_time + timedelta(minutes=55)):
                    await _send_pre_match_lineup(match=match_data, context=context)

        # Handle matches that haven't started yet
        elif now < start_time:
            # Schedule lineup posting (55 minutes before)
            lineup_time: datetime = start_time - timedelta(minutes=55)
            context.job_queue.run_once(
                callback=send_pre_match_lineup,
                when=(lineup_time - now).total_seconds(),
                data=match_data,
                name=f"match_update_{fixture['fixture_id']}_lineup",
                job_kwargs={
                    "id": f"send_pre_match_lineup_{fixture['fixture_id']}",
                    "replace_existing": True,
                },
            )

            # Schedule live monitoring
            monitor_start: datetime = start_time - timedelta(minutes=5)
            context.job_queue.run_repeating(
                callback=monitor_live_events,
                interval=30,
                first=(monitor_start - now).total_seconds(),
                data=match_data,
                name=f"match_update_{fixture['fixture_id']}_monitor",
                job_kwargs={
                    "id": f"monitor_live_events_{fixture['fixture_id']}",
                    "replace_existing": True,
                },
            )

        # Schedule post-match stats (either immediately or at scheduled time)
        stats_time: datetime = start_time + timedelta(hours=2)
        if status == "FT":
            # Match already finished, post stats now
            await _send_post_match_stats(match=match_data, context=context)
        else:
            # Schedule normal stats posting
            context.job_queue.run_once(
                callback=send_post_match_stats,
                when=(stats_time - now).total_seconds(),
                data=match_data,
                name=f"match_update_{fixture['fixture_id']}_stats",
                job_kwargs={
                    "id": f"send_post_match_stats_{fixture['fixture_id']}",
                    "replace_existing": True,
                },
            )

    # Send confirmation with status information
    match_list = []
    for fixture in fixtures:
        status = get_fixture_status(fixture["fixture_id"])
        status_emoji = {
            "NS": "⏳",
            "1H": "⚽ 1H",
            "HT": "⏸ HT",
            "2H": "⚽ 2H",
            "FT": "✅ FT",
        }.get(status, "❓")

        match_list.append(
            f"• {status_emoji} {fixture['home_team']} vs {fixture['away_team']} "
            f"({fixture['league_name']}) at {fixture['start_time'].strftime('%H:%M')}"
        )

    await context.bot.send_message(
        chat_id=Config.MONITOR_GROUP_ID,
        text=(
            f"📅 <b>Today's Matches:</b>\n\n" + "\n".join(match_list) + "\n\n"
            f"Total matches: {len(fixtures)}\n"
            f"⏰ Last update: {now.strftime('%H:%M')}"
        ),
    )


async def send_pre_match_lineup(context: ContextTypes.DEFAULT_TYPE):
    match = context.job.data
    await _send_pre_match_lineup(match=match, context=context)


async def _send_pre_match_lineup(match, context: ContextTypes.DEFAULT_TYPE):
    home_lineup, away_lineup = get_fixture_lineups(match["fixture_id"])

    if home_lineup and away_lineup:
        message = (
            f"⚠️ <b>Lineups for {match['home_team']} vs {match['away_team']}</b> ⚠️\n\n"
            f"{home_lineup}\n\n"
            f"{away_lineup}\n\n"
            f"⏰ Match starts at <code>{match['start_time'].strftime('%H:%M')}</code>"
        )

        await context.bot.send_message(
            chat_id=Config.MONITOR_GROUP_ID,
            text=message,
        )


async def send_post_match_stats(context: ContextTypes.DEFAULT_TYPE):
    match = context.job.data
    await _send_post_match_stats(match=match, context=context)


async def _send_post_match_stats(match, context: ContextTypes.DEFAULT_TYPE):
    stats_data = get_fixture_stats(match["fixture_id"])

    if stats_data:
        message = build_match_stats_message_from_json(stats_data)
        await context.bot.send_message(
            chat_id=Config.MONITOR_GROUP_ID,
            text=message,
        )
