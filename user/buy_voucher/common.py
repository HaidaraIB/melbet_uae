import openai
from Config import Config
from client.client_calls.common import openai
import json
import models
from user.buy_voucher.constants import *
from user.buy_voucher.api_calls import *

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


async def summarize_fixtures_with_odds_stats(fixtures: dict, max_limit: int = 10):
    summary = ""

    for fix in fixtures[:max_limit]:
        fixture_id = fix["fixture"]["id"]
        home = fix["teams"]["home"]
        away = fix["teams"]["away"]
        home_name = home["name"]
        away_name = away["name"]
        match = f"{home_name} vs {away_name}"
        date = fix["fixture"]["date"][:16].replace("T", " ")
        league = fix["league"]["name"]

        summary += f"\n=== {match} | {league} | {date} ===\n"

        # ============ STANDINGS ============
        try:
            standings = await get_standings(
                fix["league"]["id"], fix["league"]["season"]
            )
            home_stand = next(
                team for team in standings if team["team"]["id"] == home["id"]
            )
            away_stand = next(
                team for team in standings if team["team"]["id"] == away["id"]
            )

            summary += "Standings:\n"
            summary += f"- {home_name}: Rank {home_stand['rank']} | {home_stand['points']} pts | {home_stand['all']['win']}W-{home_stand['all']['draw']}D-{home_stand['all']['lose']}L\n"
            summary += f"- {away_name}: Rank {away_stand['rank']} | {away_stand['points']} pts | {away_stand['all']['win']}W-{away_stand['all']['draw']}D-{away_stand['all']['lose']}L\n"

            if abs(home_stand["points"] - away_stand["points"]) >= 3:
                pressure_team = (
                    home_name
                    if home_stand["points"] < away_stand["points"]
                    else away_name
                )
                summary += (
                    f"Motivation: {pressure_team} appears under more pressure to win.\n"
                )
        except:
            summary += "Standings: Not available.\n"

        # ============ ODDS ============
        odds_list = await get_fixture_odds(fixture_id)
        summary += "\nOdds:\n"
        markets_needed = {
            "Match Winner": "1X2",
            "Over/Under": "Over/Under",
            "Both Teams To Score": "BTTS",
            "Draw No Bet": "Draw No Bet",
            "Half Time / Full Time": "HT/FT",
        }
        markets_printed = set()

        for odds_pack in odds_list:
            for bookmaker in odds_pack.get("bookmakers", []):
                for market in bookmaker.get("bets", []):
                    name = market.get("name")
                    if name in markets_needed and name not in markets_printed:
                        markets_printed.add(name)
                        values = market.get("values", [])
                        formatted = " | ".join(
                            f"{v['value']}: {v['odd']}" for v in values
                        )
                        summary += f"- {markets_needed[name]}: {formatted}\n"

        if not markets_printed:
            summary += "- Odds not available\n"

        # ============ TEAM STATS ============
        def extract_team_stats(data, team_label):
            stats = f"{team_label} Stats:\n"
            stats += f"- Avg Goals Scored: {data['goals']['for']['average']['total']}\n"
            stats += f"- Avg Goals Conceded: {data['goals']['against']['average']['total']}\n"
            stats += f"- Clean Sheets: {data['clean_sheet']['total']}\n"
            stats += f"- Failed to Score: {data['failed_to_score']['total']}\n"
            stats += f"- BTTS Rate: {data['both_teams_to_score']['percentage']}%\n"
            stats += f"- Over 2.5 Matches: {data['fixtures']['over_25']}\n"
            return stats

        try:
            stats_home = await get_team_stats(
                home["id"], fix["league"]["id"], fix["league"]["season"]
            )
            stats_away = await get_team_stats(
                away["id"], fix["league"]["id"], fix["league"]["season"]
            )
            summary += "\n" + extract_team_stats(stats_home, home_name) + "\n"
            summary += extract_team_stats(stats_away, away_name) + "\n"
        except:
            summary += "\nStats: Not available.\n"

        # ============ H2H ============
        try:
            h2h = await get_h2h(home["id"], away["id"])
            summary += "Last 5 Head-to-Head:\n"
            for m in h2h[:5]:
                h = m["teams"]["home"]["name"]
                a = m["teams"]["away"]["name"]
                gh = m["goals"]["home"]
                ga = m["goals"]["away"]
                summary += f"- {h} {gh} - {ga} {a}\n"
        except:
            summary += "Head-to-Head: Not available.\n"

        # ============ LAST RESULTS ============
        def format_last_results(results, team_label):
            line = f"{team_label} Last 5 Matches: "
            for m in results[:5]:
                g = m.get("goals", {})
                score = f"{g.get('for', '?')}-{g.get('against', '?')}"
                line += score + " | "
            return line.strip(" | ") + "\n"

        try:
            last_home = await get_last_results(home["id"])
            last_away = await get_last_results(away["id"])
            summary += format_last_results(last_home, home_name)
            summary += format_last_results(last_away, away_name)
        except:
            summary += "Recent Form: Not available.\n"

        summary += "\n" + "=" * 50 + "\n"

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
