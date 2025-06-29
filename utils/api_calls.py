import aiohttp
from datetime import datetime, timedelta
from Config import Config
from telegram.ext import ContextTypes
from telegram import InputMediaPhoto
from common.constants import *
from client.client_calls.constants import openai
from utils.functions import (
    generate_infographic,
    draw_double_lineup_image,
    filter_fixtures,
    build_enhanced_poster_prompt,
)
from utils.helpers import _get_request, BASE_URL
import logging
import models
from io import BytesIO

log = logging.getLogger(__name__)


async def get_fixture_lineups(fixture_id: int) -> tuple:
    url = f"{BASE_URL}/fixtures/lineups"
    querystring = {"fixture": fixture_id}

    try:

        data = await _get_request(url, querystring)

        if not data:
            return None, None

        home = data[0]
        away = data[1]

        return home, away
    except Exception as e:
        log.error(f"Error fetching lineups: {e}")
        return None, None


async def get_fixture_stats(fixture_id: int) -> dict:
    url = f"{BASE_URL}/fixtures/statistics"
    querystring = {"fixture": fixture_id}

    response = await _get_request(url, querystring)
    with models.session_scope() as s:
        existing_fix_stats = (
            s.query(models.CachedFixtureStats).filter_by(fixture_id=fixture_id).first()
        )
        if not existing_fix_stats:
            s.add(
                models.CachedFixtureStats(
                    fixture_id=fixture_id,
                    data=response,
                    last_updated=datetime.now(),
                )
            )
        else:
            existing_fix_stats.data = response
            existing_fix_stats.last_updated = datetime.now()
        s.commit()
    return response


async def get_fixture_events(fixture_id: int) -> list:
    url = f"{BASE_URL}/fixtures/events"
    querystring = {"fixture": fixture_id}

    return await _get_request(url=url, params=querystring)


async def get_daily_fixtures() -> list[dict]:
    now = datetime.now(TIMEZONE)
    today = now.strftime("%Y-%m-%d")
    all_fixtures = []

    url = f"{BASE_URL}/fixtures"
    querystring = {
        "date": today,
        "timezone": TIMEZONE_NAME,
    }

    try:
        fixtures = await _get_request(url, querystring)
        for fixture in fixtures:
            all_fixtures.append(_extract_fixture_data(fixture=fixture))
    except Exception as e:
        log.error(f"Error fetching fixtures: {e}")

    return filter_fixtures(all_fixtures)


def _extract_fixture_data(fixture: dict):
    return {
        "fixture_id": fixture["fixture"]["id"],
        "home_team": fixture["teams"]["home"]["name"],
        "away_team": fixture["teams"]["away"]["name"],
        "start_time": datetime.fromtimestamp(
            fixture["fixture"]["timestamp"], tz=TIMEZONE
        ),
        "league_id": fixture["league"]["id"],
        "league_name": fixture["league"]["name"],
    }


async def get_fixture_status(fixture_id: int) -> str:
    url = f"{BASE_URL}/fixtures"
    querystring = {"id": fixture_id}

    try:
        data = await _get_request(url, querystring)
        return data[0]["fixture"]["status"]["short"]  # FT, NS, 1H, HT, etc.
    except Exception as e:
        log.error(f"Error checking fixture status: {e}")
        return "UNKNOWN"


async def get_fixture(fixture_id: int):
    url = f"{BASE_URL}/fixtures"
    querystring = {"id": fixture_id}

    return await _get_request(url, querystring)


# region Jobs


async def monitor_live_events(context: ContextTypes.DEFAULT_TYPE):
    """Enhanced monitoring with match completion detection"""
    match = context.job.data["match"]

    # First check if match has ended
    status = await get_fixture_status(match["fixture_id"])
    if status == "FT":
        # Match finished, post stats and remove monitoring job
        await _send_post_match_stats(fixture_id=match["fixture_id"], context=context)
        context.job.schedule_removal()
        return

    # Proceed with normal event monitoring if match is still ongoing
    events = await get_fixture_events(match["fixture_id"])

    if not events:
        return

    last_event_id = match.get("last_event_id", 0)
    for event in events[last_event_id + 1 :]:
        if event["type"].lower() in ["goal", "redcard", "penalty"]:
            emoji = {"goal": "⚽", "redcard": "🟥", "penalty": "🎯"}.get(
                event["type"].lower(), "ℹ"
            )

            message = (
                f"{emoji} <b>{event['type'].upper()}</b> {emoji}\n"
                f"<b>{event['player']['name']}</b> ({event['team']['name']})\n"
                f"⏱️ Minute: <code>{event['time']['elapsed']}'</code>"
            )
            for chat_id in MONITOR_GROUPS:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                )
            match["last_event_id"] = events.index(event)

    context.job_queue.run_once(
        callback=monitor_live_events,
        when=10,
        data={
            "match": match,
        },
        name=f"match_update_{match['fixture_id']}_monitor",
        job_kwargs={
            "id": f"monitor_live_events_{match['fixture_id']}",
            "replace_existing": True,
        },
    )


async def schedule_daily_fixtures(context: ContextTypes.DEFAULT_TYPE):
    # Get today's fixtures
    fixtures = await get_daily_fixtures()

    if not fixtures:
        return

    # Schedule updates for each match with lost time handling
    now = datetime.now(TIMEZONE)
    for fixture in fixtures:
        status = await get_fixture_status(fixture["fixture_id"])

        match_data = {
            **fixture,
            "last_event_id": 0,
        }
        start_time: datetime = fixture["start_time"]

        # Handle matches that already started but haven't finished
        if start_time <= now <= (start_time + timedelta(hours=3)):

            if status != "FT":
                # Match is in progress, schedule immediate monitoring
                context.job_queue.run_once(
                    callback=monitor_live_events,
                    when=10,
                    data={
                        "match": match_data,
                    },
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
                data={
                    "match": match_data,
                },
                name=f"match_update_{fixture['fixture_id']}_lineup",
                job_kwargs={
                    "id": f"send_pre_match_lineup_{fixture['fixture_id']}",
                    "replace_existing": True,
                },
            )

            # Schedule live monitoring
            monitor_start: datetime = start_time - timedelta(minutes=5)
            context.job_queue.run_once(
                callback=monitor_live_events,
                when=(monitor_start - now).total_seconds(),
                data={
                    "match": match_data,
                },
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
            await _send_post_match_stats(
                fixture_id=match_data["fixture_id"], context=context
            )

    # Send confirmation with status information
    match_list = []
    for fixture in fixtures:
        status = await get_fixture_status(fixture["fixture_id"])
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

    for chat_id in MONITOR_GROUPS:
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"📅 <b>Today's Matches:</b>\n\n" + "\n".join(match_list) + "\n\n"
                f"Total matches: {len(fixtures)}\n"
                f"⏰ Last update: {now.strftime('%H:%M')}"
            ),
        )


async def send_pre_match_lineup(context: ContextTypes.DEFAULT_TYPE):
    match = context.job.data["match"]
    await _send_pre_match_lineup(match=match, context=context)


async def _send_pre_match_lineup(match, context: ContextTypes.DEFAULT_TYPE):
    home_lineup_data, away_lineup_data = await get_fixture_lineups(match["fixture_id"])

    if home_lineup_data and away_lineup_data:

        def extract_players(team_data):
            return [
                {"number": p["player"]["number"], "name": p["player"]["name"]}
                for p in team_data["startXI"]
            ]

        # Generate lineup image for both teams on one field
        lineup_img = draw_double_lineup_image(
            home_team=match["home_team"],
            away_team=match["away_team"],
            formation_home=home_lineup_data["formation"],
            formation_away=away_lineup_data["formation"],
            coach_home=home_lineup_data["coach"]["name"],
            coach_away=away_lineup_data["coach"]["name"],
            players_home=extract_players(home_lineup_data),
            players_away=extract_players(away_lineup_data),
        )

        players_home_list = ", ".join(
            p["name"] for p in extract_players(home_lineup_data)
        )
        players_away_list = ", ".join(
            p["name"] for p in extract_players(away_lineup_data)
        )

        prompt = (
            f"The confirmed lineups for {match['home_team']} vs {match['away_team']} are set.\n"
            f"Home formation: {home_lineup_data['formation']} (coach: {home_lineup_data['coach']['name']})\n"
            f"Home lineup: {players_home_list}\n"
            f"Away formation: {away_lineup_data['formation']} (coach: {away_lineup_data['coach']['name']})\n"
            f"Away lineup: {players_away_list}\n\n"
            "Write a short, exciting 3-line analysis for fans that includes:\n"
            "1. Tactical expectations from formations\n"
            "2. Possible impact players ONLY from the confirmed lineup\n"
            "3. End with: 'Want exclusive pre-match insights? Get your Player account through us now!'"
        )

        response = await openai.chat.completions.create(
            model='o3-pro',
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_tokens=150,
        )

        analysis = response.choices[0].message.content.strip()

        for chat_id in MONITOR_GROUPS:
            lineup_img.seek(0)
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=lineup_img,
                caption=(
                    f"⚠️ <b>{match['home_team']} vs {match['away_team']} - Confirmed Lineups</b>\n\n"
                    f"{analysis}\n\n⏰ Kickoff at <code>{match['start_time'].strftime('%H:%M')}</code>"
                ),
                parse_mode="HTML",
            )


async def _send_post_match_stats(fixture_id: int, context: ContextTypes.DEFAULT_TYPE):
    stats_data = await get_fixture_stats(fixture_id)

    if stats_data:
        team1, stats1, team2, stats2 = extract_stats(stats_data)
        summary_stats = generate_summary_stats(
            team1=team1, team2=team2, stats1=stats1, stats2=stats2
        )
        summary = await generate_match_summary(
            team1=team1, team2=team2, summary_stats=summary_stats
        )
        infographic = generate_infographic(
            team1=team1, stats1=stats1, team2=team2, stats2=stats2
        )
        for chat_id in MONITOR_GROUPS:
            infographic.seek(0)
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=infographic,
                caption=summary,
            )


async def post_in_groups(
    context: ContextTypes.DEFAULT_TYPE,
    team1: str,
    team2: str,
    league: dict,
    d: str,
    infographic: BytesIO,
    stats: str,
):
    try:
        with models.session_scope() as s:
            subs = (
                s.query(models.GroupSubscription)
                .filter_by(is_active=True, status="active")
                .all()
            )

            # Make sure infographic is at position 0
            infographic.seek(0)

            for sub in subs:
                pref = (
                    s.query(models.GroupPreferences)
                    .filter_by(group_id=sub.group_id)
                    .first()
                )

                # Check sport and league preferences
                sport_check, league_check = False, False
                if not pref or not pref.sports:
                    sport_check, league_check = True, True
                else:
                    for sport, leagues in (pref.sports or {}).items():
                        if sport == "football":
                            sport_check = True
                            if not leagues or league["id"] in leagues:
                                league_check = True
                                break

                if sport_check and league_check:
                    try:
                        # Generate branding image
                        img_prompt = build_enhanced_poster_prompt(
                            match_title=f"{team1} vs {team2}",
                            league_name=league["name"],
                            match_datetime=d,
                            stats_summary=stats,
                            brands=pref.brands,
                        )
                        image = await openai.images.generate(
                            model=Config.DALL_E_MODEL,
                            prompt=img_prompt,
                            n=1,
                            size="1024x1024",
                        )

                        async with aiohttp.ClientSession() as session:
                            async with session.get(image.data[0].url) as response:
                                image_data = await response.read()
                                branding_image = BytesIO(image_data)
                                branding_image.seek(0)

                        async def generate_group_summary(
                            team1: str,
                            team2: str,
                            stats: str,
                            prefs: models.GroupPreferences,
                        ):
                            prompt = (
                                f"Write a short match summary for {team1} vs {team2}.\n"
                                f"Language: {prefs.language}, Dialect: {prefs.dialect}.\n"
                                f"Stats: {stats}\n"
                                "Style: Enthusiastic, engaging for betting group."
                            )
                            summary = await openai.chat.completions.create(
                                model=Config.GPT_MODEL,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": prompt,
                                    },
                                ],
                                max_completion_tokens=150,
                            )
                            return summary.choices[0].message.content.strip()

                        # Generate summary
                        summary = await generate_group_summary(
                            team1=team1, team2=team2, stats=stats, prefs=pref
                        )

                        # Make sure infographic is at position 0 again
                        infographic.seek(0)

                        await context.bot.send_media_group(
                            chat_id=sub.group_id,
                            media=[
                                InputMediaPhoto(media=infographic),
                                InputMediaPhoto(media=branding_image),
                            ],
                            caption=summary,
                        )
                    except Exception as e:
                        log.error(f"Error posting to group {sub.group_id}: {str(e)}")
                        continue
    except Exception as e:
        log.error(f"Error in post_in_groups: {str(e)}")
        raise


def extract_stats(json_data: list[dict]):
    team1 = json_data[0]["team"]["name"]
    stats1 = {item["type"]: item["value"] for item in json_data[0]["statistics"]}
    team2 = json_data[1]["team"]["name"]
    stats2 = {item["type"]: item["value"] for item in json_data[1]["statistics"]}
    return team1, stats1, team2, stats2


def generate_summary_stats(team1: str, team2: str, stats1: dict, stats2: dict):
    summary_stats = []
    for key in ["Ball Possession", "Total Shots", "Passes %", "Shots on Goal"]:
        val1 = stats1.get(key, "N/A")
        val2 = stats2.get(key, "N/A")
        summary_stats.append(f"- {key}: {team1} ({val1}) / {team2} ({val2})")
    return summary_stats


async def generate_match_summary(team1: str, team2: str, summary_stats: list):
    match_details = (
        f"Match: {team1} vs {team2}\n" "Stats:\n" f"{"\n".join(summary_stats)}\n\n"
    )
    with models.session_scope() as s:
        prompt = s.get(models.Setting, "gpt_prompt_match_summary")
        if prompt:
            prompt = prompt.value
        else:
            prompt = (
                "You're a smart football analyst writing a short match summary.\n\n"
                "Write a concise, stylish summary in English (max 4 lines) that:\n"
                "- Starts with storytelling (not just stats)\n"
                "- Weaves in some of the stats smoothly\n"
                "- Ends with a soft CTA inviting the reader to create a Player account to access pre-match insights and analysis\n\n"
                "Avoid exaggeration or direct 'betting' words. Use a confident, professional tone."
            )

    response = await openai.chat.completions.create(
        model=Config.GPT_MODEL,
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": match_details,
            },
        ],
        max_completion_tokens=150,
    )

    cta = (
        "\n\n"
        "Want to see the full picture before kickoff?\n"
        "Request your Player account through us and receive:\n"
        "— Pre-match insights\n"
        "— Tactical breakdowns\n"
        "— Exclusive strategic advantages\n"
        "<i>Only for our users.</i>"
    )

    return response.choices[0].message.content.strip() + cta
