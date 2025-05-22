import openai
from Config import Config
from client.client_calls.common import openai
import json
import models
from user.buy_voucher.constants import *
from user.buy_voucher.api_calls import *
import logging

log = logging.getLogger(__name__)

def extract_ids(preferences: str):
    text = preferences.lower()
    league_id = None
    team_id = None

    for key, val in LEAGUE_MAP.items():
        if key in text:
            league_id = val
            break
    for key, val in TEAM_MAP.items():
        if key in text:
            team_id = val
            break
    return league_id, team_id


async def get_last_matches_stats(team_id: int, last_matches: list) -> list:
    IMPORTANT_STATS = [
        "Total Corners",
        "Yellow Cards",
        "Red Cards",
        "Offsides",
        "Fouls",
        "Shots on Target",
        "Ball Possession",
    ]
    detailed_stats = []

    async def fetch_single_match_stats(match):
        fixture_id = match["fixture"]["id"]
        try:
            stats = await get_fixture_stats(fixture_id)
            team_stats = next((s for s in stats if s["team"]["id"] == team_id), None)
            if not team_stats:
                return None
            filtered_stats = {
                s["type"]: s["value"]
                for s in team_stats["statistics"]
                if s["type"] in IMPORTANT_STATS
            }
            return {
                "fixture_id": fixture_id,
                "vs": f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}",
                "date": match["fixture"]["date"],
                "stats": filtered_stats,
            }
        except Exception as e:
            log.error(f"Failed to fetch stats for fixture {fixture_id}: {e}")
            return None

    # اجمع النتائج باستخدام asyncio.gather لتسريع الأداء
    tasks = [fetch_single_match_stats(m) for m in last_matches[:5]]
    results = await asyncio.gather(*tasks)

    # تجاهل القيم الفارغة
    detailed_stats = [r for r in results if r]

    return detailed_stats


def is_match_data_complete(match: str) -> bool:
    """
    يتحقق من أن كل مباراة تحتوي على البيانات الأساسية اللازمة
    لتوليد توقعات تحليلية دقيقة.
    """
    has_standings = "Rank" in match or "points" in match
    has_team_stats = "Goals For" in match or "Clean Sheets" in match
    has_match_stats = (
        "Fouls" in match or "Total Corners" in match or "Yellow Cards" in match
    )
    has_form = "Last 5" in match
    return has_standings and has_team_stats and has_match_stats and has_form


async def summarize_fixtures_with_odds_stats(fixtures: list, max_limit: int = 5) -> str:
    summary = ""

    for fix in fixtures[:max_limit]:
        fix_summary = ""
        fixture_id = fix["fixture"]["id"]
        home = fix["teams"]["home"]
        away = fix["teams"]["away"]
        league = fix["league"]
        date = fix["fixture"]["date"][:16].replace("T", " ")
        fix_summary += (
            f"\n=== {home['name']} vs {away['name']} | {league['name']} | {date} ===\n"
        )

        # STANDINGS
        try:
            standings = await get_standings(league["id"], league["season"])
            home_stand = next(t for t in standings if t["team"]["id"] == home["id"])
            away_stand = next(t for t in standings if t["team"]["id"] == away["id"])
            fix_summary += "Standings:\n"
            fix_summary += f"- {home['name']}: Rank {home_stand['rank']} | {home_stand['points']} pts\n"
            fix_summary += f"- {away['name']}: Rank {away_stand['rank']} | {away_stand['points']} pts\n"
        except Exception as e:
            standings_error = "Standings: Not available\n"
            log.error(f"{standings_error}: {e}")
            fix_summary += standings_error

        # ODDS
        odds_data = await get_fixture_odds(fixture_id)
        fix_summary += "\nOdds:\n"
        markets_needed = {
            "Match Winner": "1X2",
            "Over/Under": "Goals",
            "Total Corners": "Corners",
            "Total Cards": "Cards",
            "Draw No Bet": "DNB",
            "Both Teams To Score": "BTTS",
        }
        printed = set()
        for provider in odds_data:
            for book in provider.get("bookmakers", []):
                for market in book.get("bets", []):
                    name = market.get("name")
                    if name in markets_needed and name not in printed:
                        printed.add(name)
                        values = " | ".join(
                            f"{v['value']}: {v['odd']}" for v in market["values"]
                        )
                        fix_summary += f"- {markets_needed[name]}: {values}\n"
        if not printed:
            fix_summary += "- Odds not available\n"

        # TEAM STATS
        try:
            stats_home = await get_team_stats(
                home["id"], league["id"], league["season"]
            )
            stats_away = await get_team_stats(
                away["id"], league["id"], league["season"]
            )

            def team_stats_block(stats, label):
                return (
                    f"{label} Stats:\n"
                    f"- Goals For: {stats['goals']['for']['average']['total']}\n"
                    f"- Goals Against: {stats['goals']['against']['average']['total']}\n"
                    f"- Clean Sheets: {stats['clean_sheet']['total']}\n"
                    f"- Failed to Score: {stats['failed_to_score']['total']}\n"
                    f"- BTTS %: {stats['both_teams_to_score']['percentage'] if stats.get("both_teams_to_score", None) else None}\n"
                )

            fix_summary += (
                "\n"
                + team_stats_block(stats_home, home["name"])
                + team_stats_block(stats_away, away["name"])
            )
        except Exception as e:
            stats_error = "\nStats: Not available\n"
            log.error(f"{stats_error}: {e}")
            fix_summary += stats_error

        # FIXTURE STATS
        try:
            fixture_stats = await get_fixture_stats(fixture_id)
            fix_summary += "Match Stats:\n"
            for team_stats in fixture_stats:
                team_name = team_stats["team"]["name"]
                stats_lines = [
                    f"  • {s['type']}: {s['value']}"
                    for s in team_stats.get("statistics", [])[:5]
                ]
                fix_summary += f"- {team_name}:\n" + "\n".join(stats_lines) + "\n"
        except Exception as e:
            match_stats_error = "Match Stats: Not available\n"
            log.error(f"{match_stats_error}: {e}")
            fix_summary += match_stats_error

        # H2H
        try:
            h2h = await get_h2h(home["id"], away["id"])
            fix_summary += "Last 5 Head-to-Head:\n"
            for h in h2h[:5]:
                h_name = h["teams"]["home"]["name"]
                a_name = h["teams"]["away"]["name"]
                gh = h["goals"]["home"]
                ga = h["goals"]["away"]
                fix_summary += f"- {h_name} {gh} - {ga} {a_name}\n"
        except Exception as e:
            h2h_error = "H2H: Not available\n"
            log.error(f"{h2h_error}: {e}")
            fix_summary += h2h_error

        # FORM
        try:

            def form_block(matches, team_id: int, label: str) -> str:
                results = []
                for m in matches[:5]:
                    is_home = m["teams"]["home"]["id"] == team_id
                    goals_for = m["goals"]["home"] if is_home else m["goals"]["away"]
                    goals_against = (
                        m["goals"]["away"] if is_home else m["goals"]["home"]
                    )
                    venue = "H" if is_home else "A"  # H = Home, A = Away
                    outcome = (
                        "W"
                        if goals_for > goals_against
                        else "D" if goals_for == goals_against else "L"
                    )
                    results.append(f"{venue} {goals_for}-{goals_against} ({outcome})")
                return f"{label} Last 5: " + " | ".join(results) + "\n"

            last_home = await get_last_results(home["id"])
            last_away = await get_last_results(away["id"])

            fix_summary += form_block(last_home, home["id"], home["name"])
            fix_summary += form_block(last_away, away["id"], away["name"])

            def format_last_match_stats(label: str, matches: list) -> str:
                if not matches:
                    return f"{label} Last 5 Match Stats: Not available\n"

                text = f"{label} Last 5 Match Stats:\n"
                for m in matches:
                    text += f"- {m['vs']} ({m['date'][:10]}):\n"
                    for stat_type, val in m["stats"].items():
                        text += f"  • {stat_type}: {val}\n"
                return text

            last_home_stats = await get_last_matches_stats(home["id"], last_home)
            last_away_stats = await get_last_matches_stats(away["id"], last_away)

            fix_summary += format_last_match_stats(home["name"], last_home_stats)
            fix_summary += format_last_match_stats(away["name"], last_away_stats)
        except Exception as e:
            recent_form_error = "Recent form: Not available\n"
            log.error(f"{recent_form_error}: {e}")
            fix_summary += recent_form_error
        if is_match_data_complete(fix_summary):
            summary += fix_summary + "=" * 60 + "\n"

    return summary if summary else "No matches found."


async def generate_multimatch_coupon(fixtures_summary: str):
    json_format_instructions = (
        "\n\nImportant:\n"
        "• Return RAW JSON only in this exact format (do NOT use Arabic or alternative keys):\n"
        "{\n"
        '  "matches": [\n'
        "    {\n"
        '      "teams": "Team A vs Team B",\n'
        '      "tips": [\n'
        '        {"risk": "Low", "market": "...", "selection": "...", "probability": 60, "odds": 1.8, "value": "✅", "reason": "..."},\n'
        '        {"risk": "Medium", ...},\n'
        '        {"risk": "High", ...}\n'
        "      ]\n"
        "    }\n"
        "  ],\n"
        '  "combo": { "selections": ["...","..."], "combined_odds": 4.5, "overall_risk": "Medium", "reason": "..." }\n'
        "}\n"
        "Then after --- send a user-friendly Markdown summary (in English).\n"
        "Start your answer with { and do NOT put code blocks or explanations before or after the JSON.\n\n"
    )

    with models.session_scope() as s:
        voucher_prompt = s.get(models.Setting, "gpt_prompt_voucher")
        default_prompt = s.get(models.Setting, "gpt_prompt")
        p = voucher_prompt.value if voucher_prompt else default_prompt.value

    prompt = f"{p}" f"{json_format_instructions}" f"Match data:\n{fixtures_summary}"

    resp = await openai.chat.completions.create(
        model=Config.GPT_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.7,
    )
    content = resp.choices[0].message.content.strip()
    if "```json" in content:
        json_part = content.split("```json")[1].split("```")[0].strip()
    else:
        json_part = content.split("---")[0].strip()
    coupon = json.loads(r"{}".format(json_part))

    md_part = ""
    if "---" in content:
        md_part = content.split("---", 1)[1].strip()
    elif "```" in content:
        # احتمال وجود Markdown بعد الكود
        after_json = content.split("`")[-1].strip()
        if after_json:
            md_part = after_json

    return coupon, md_part
