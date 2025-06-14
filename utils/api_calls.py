import aiohttp
from datetime import datetime, timedelta
from Config import Config
from telegram.ext import ContextTypes
from telegram import InputMediaPhoto
from common.constants import TIMEZONE, TIMEZONE_NAME
from client.client_calls.common import openai
from utils.functions import (
    generate_infographic,
    draw_double_lineup_image,
    filter_fixtures,
    build_enhanced_poster_prompt,
)
import logging
import asyncio
import models
from io import BytesIO

log = logging.getLogger(__name__)


BASE_URL = f"https://{Config.X_RAPIDAPI_FB_HOST}/v3"
HEADERS = {
    "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
    "X-RapidAPI-Host": Config.X_RAPIDAPI_FB_HOST,
}


async def handle_rate_limit(func, *args):
    # Handle rate limit error
    log.warning(f"Rate limited. Waiting 5 seconds...")
    await asyncio.sleep(5)
    return await func(*args)


async def _get_request(url, params, headers=HEADERS):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 429:
                    return await handle_rate_limit(_get_request, url, params, headers)
                data = await response.json()
                return data.get("response", [])

    except Exception as e:
        log.error(f"Error in _get_request: {e}")
        return []


async def get_fixture_lineups(fixture_id: int) -> tuple:
    """Fetch starting lineups for a fixture"""
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
    """Fetch statistics for a fixture"""
    url = f"{BASE_URL}/fixtures/statistics"
    querystring = {"fixture": fixture_id}

    return await _get_request(url, querystring)


async def get_fixture_events(fixture_id: int) -> list:
    """Fetch events for a fixture"""
    url = f"{BASE_URL}/fixtures/events"
    querystring = {"fixture": fixture_id}

    return await _get_request(url=url, params=querystring)


async def get_daily_fixtures() -> list[dict]:
    """Fetch all fixtures for today across important leagues"""
    now = datetime.now(TIMEZONE)
    today = now.strftime("%Y-%m-%d")
    all_fixtures = []

    url = f"{BASE_URL}/fixtures"
    querystring = {
        "date": today,
        "timezone": TIMEZONE_NAME,
    }

    try:
        fixtures = filter_fixtures(await _get_request(url, querystring))
        for fixture in fixtures:
            all_fixtures.append(_extract_fixture_data(fixture=fixture))
    except Exception as e:
        log.error(f"Error fetching fixtures: {e}")

    return all_fixtures


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
    """Check if fixture has ended"""
    url = f"{BASE_URL}/fixtures"
    querystring = {"id": fixture_id}

    try:
        data = await _get_request(url, querystring)
        return data[0]["fixture"]["status"]["short"]  # FT, NS, 1H, HT, etc.
    except Exception as e:
        log.error(f"Error checking fixture status: {e}")
        return "UNKNOWN"


async def get_fixture(fixture_id: int):
    """Check if fixture has ended"""
    url = f"{BASE_URL}/fixtures"
    querystring = {"id": fixture_id}

    return await _get_request(url, querystring)


# region Jobs


async def monitor_live_events(context: ContextTypes.DEFAULT_TYPE):
    """Enhanced monitoring with match completion detection"""
    match = context.job.data["match"]
    chat_id = context.job.data["chat_id"]

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
                chat_id=chat_id,
                text=message,
            )
            match["last_event_id"] = event["id"]


async def schedule_daily_fixtures(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data["chat_id"]
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
                context.job_queue.run_repeating(
                    callback=monitor_live_events,
                    interval=30,
                    first=30,
                    data={
                        "match": match_data,
                        "chat_id": chat_id,
                    },
                    name=f"match_update_{fixture['fixture_id']}_monitor_{chat_id}",
                    job_kwargs={
                        "id": f"monitor_live_events_{fixture['fixture_id']}_{chat_id}",
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
                    "chat_id": chat_id,
                },
                name=f"match_update_{fixture['fixture_id']}_lineup_{chat_id}",
                job_kwargs={
                    "id": f"send_pre_match_lineup_{fixture['fixture_id']}_{chat_id}",
                    "replace_existing": True,
                },
            )

            # Schedule live monitoring
            monitor_start: datetime = start_time - timedelta(minutes=5)
            context.job_queue.run_repeating(
                callback=monitor_live_events,
                interval=30,
                first=(monitor_start - now).total_seconds(),
                data={
                    "match": match_data,
                    "chat_id": chat_id,
                },
                name=f"match_update_{fixture['fixture_id']}_monitor_{chat_id}",
                job_kwargs={
                    "id": f"monitor_live_events_{fixture['fixture_id']}_{chat_id}",
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
        else:
            # Schedule normal stats posting
            context.job_queue.run_once(
                callback=send_post_match_stats,
                when=(stats_time - now).total_seconds(),
                data={
                    "match": match_data,
                    "chat_id": chat_id,
                },
                name=f"match_update_{fixture['fixture_id']}_stats_{chat_id}",
                job_kwargs={
                    "id": f"send_post_match_stats_{fixture['fixture_id']}_{chat_id}",
                    "replace_existing": True,
                },
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
    chat_id = context.job.data["chat_id"]
    await _send_pre_match_lineup(match=match, context=context, chat_id=chat_id)


async def _send_pre_match_lineup(
    match,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int = Config.UAE_MONITOR_GROUP_ID,
):
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

        # img_prompt = f"A dynamic sports-themed illustration showing two soccer teams lined up facing each other. The left side shows the home team with formation {home_lineup_data['formation']}, coached by {home_lineup_data['coach']['name']}, and the right side shows the away team with formation {away_lineup_data['formation']}, coached by {away_lineup_data['coach']['name']}. The background features a packed stadium under night lights. Overlay tactical arrows, players in action stances, and highlight 1-2 star players from each team with a glow effect. Include bold, modern text at the bottom: “Want exclusive pre-match insights? Get your MELBET account through us now!” - keep the style cinematic and dramatic."
        # lineup_img = await openai.images.generate(
        #     model=Config.DALL_E_MODEL,
        #     prompt=img_prompt,
        #     n=1,
        #     size="1024x1024",
        # )
        # image_data = requests.get(lineup_img.data[0].url).content

        await context.bot.send_photo(
            chat_id=chat_id,
            photo=lineup_img,
            caption=f"⚠️ <b>{match['home_team']} vs {match['away_team']} - Confirmed Lineups</b>",
            parse_mode="HTML",
        )

        # GPT analysis prompt
        prompt = (
            f"The confirmed lineups for {match['home_team']} vs {match['away_team']} "
            f"are set.\nHome formation: {home_lineup_data['formation']} (coach: {home_lineup_data['coach']['name']})\n"
            f"Away formation: {away_lineup_data['formation']} (coach: {away_lineup_data['coach']['name']})\n\n"
            "Write a short, exciting 3-line analysis for fans that includes:\n"
            "1. Tactical expectations from formations\n"
            "2. Possible impact players\n"
            "3. End with: 'Want exclusive pre-match insights? Get your Player account through us now!'"
        )

        response = await openai.chat.completions.create(
            model=Config.GPT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_tokens=150,
        )

        analysis = response.choices[0].message.content.strip()

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"{analysis}\n\n⏰ Kickoff at <code>{match['start_time'].strftime('%H:%M')}</code>",
            parse_mode="HTML",
        )


async def send_post_match_stats(context: ContextTypes.DEFAULT_TYPE):
    match = context.job.data["match"]
    chat_id = context.job.data["chat_id"]
    await _send_post_match_stats(
        fixture_id=match["fixture_id"], context=context, chat_id=chat_id
    )


async def _send_post_match_stats(
    fixture_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int = Config.UAE_MONITOR_GROUP_ID,
):
    fix_data = await get_fixture(fixture_id)
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
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=infographic,
            caption=summary,
        )
        asyncio.create_task(
            post_in_groups(
                context=context,
                team1=team1,
                team2=team2,
                league=fix_data[0]["league"],
                d=fix_data[0]["fixture"]["date"],
                infographic=infographic,
                stats=summary_stats,
            )
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
