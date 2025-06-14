from Config import Config
from client.client_calls.common import openai
from utils.api_calls_by_sport import (
    get_fixture_odds_by_sport,
    get_h2h_by_sport,
    get_team_statistics_by_sport,
    get_team_standing_by_sport,
    get_last_matches_by_sport,
)
from utils.api_calls import get_fixture_stats
from utils.functions import (
    format_basketball_stats,
    format_american_football_stats,
    format_hockey_stats,
    format_football_stats,
    format_last_matches,
    structure_team_standing,
    summarize_odds,
)
import json
import logging

log = logging.getLogger(__name__)


async def summarize_fixtures_with_odds_stats(fixtures: list) -> str:
    summary = ""
    for fix in fixtures:
        fix_summary = ""
        fixture_id = fix["fixture_id"]
        home_name = fix["home_name"]
        home_id = fix["home_id"]
        away_name = fix["away_name"]
        away_id = fix["away_id"]
        league_id = fix["league_id"]
        league_name = fix["league_name"]
        date = fix["date"][:16].replace("T", " ")
        season = fix["season"]
        fix_summary += f"\n=== Home Team: {home_name} vs Away Team: {away_name} | {league_name} | {date} ===\n"

        # STANDINGS
        home_stand = structure_team_standing(
            data=await get_team_standing_by_sport(
                team_id=home_id, league_id=league_id, season=season, sport=fix["sport"]
            ),
            sport=fix["sport"],
        )
        away_stand = structure_team_standing(
            data=await get_team_standing_by_sport(
                team_id=away_id, league_id=league_id, season=season, sport=fix["sport"]
            ),
            sport=fix["sport"],
        )
        if home_stand and away_stand:
            fix_summary += "Standings:\n"
            fix_summary += f"- {home_name}: Rank {home_stand['rank']} | {home_stand['points']} pts\n"
            fix_summary += f"- {away_name}: Rank {away_stand['rank']} | {away_stand['points']} pts\n"
        else:
            fix_summary += "Standings: Not available\n"

        # ODDS
        odds = await get_fixture_odds_by_sport(
            fixture_id=fixture_id, sport=fix["sport"]
        )
        fix_summary += summarize_odds(odds) if odds else "- Odds not available\n"

        # TEAMS STATS
        home_stats = await get_team_statistics_by_sport(
            team_id=home_id,
            league_id=league_id,
            season=season,
            sport=fix["sport"],
            game_id=fixture_id,
        )
        away_stats = await get_team_statistics_by_sport(
            team_id=away_id,
            league_id=league_id,
            season=season,
            sport=fix["sport"],
            game_id=fixture_id,
        )
        if home_stats or away_stats:
            if home_stats:
                fix_summary += f"\n{home_name} Statistics:\n"
                if fix["sport"] == "basketball":
                    home_formatted = format_basketball_stats(stats=home_stats)
                elif fix["sport"] == "football":
                    home_formatted = format_football_stats(stats=home_stats)
                elif fix["sport"] == "american-football":
                    home_formatted = format_american_football_stats(stats=home_stats)
                elif fix["sport"] == "hockey":
                    home_formatted = format_hockey_stats(stats=home_stats)

                fix_summary += (
                    f"- {home_name}: {home_formatted}\n"
                    if home_formatted
                    else f"- {home_name}: Stats unavailable\n"
                )
            if away_stats:
                fix_summary += f"\n{away_name} Statistics:\n"
                if fix["sport"] == "basketball":
                    away_formatted = format_basketball_stats(stats=away_stats)
                elif fix["sport"] == "football":
                    away_formatted = format_football_stats(stats=away_stats)
                elif fix["sport"] == "american-football":
                    away_formatted = format_american_football_stats(stats=away_stats)
                elif fix["sport"] == "hockey":
                    away_formatted = format_hockey_stats(stats=away_stats)

                fix_summary += (
                    f"- {away_name}: {away_formatted}\n"
                    if away_formatted
                    else f"- {away_name}: Stats unavailable\n"
                )
        else:
            fix_summary += "\nTeam Statistics: Not available\n"

        # FB FIXTURE STATS
        if fix["sport"] == "football":
            fix_stats = await get_fixture_stats(fixture_id=fixture_id)
            if fix_stats:
                fix_summary += "\nMatch Stats:\n"
                for team_stats in fix_stats:
                    team_name = team_stats["team"]["name"]
                    stats_lines = [
                        f"  • {s['type']}: {s['value']}"
                        for s in team_stats.get("statistics", [])[:5]
                    ]
                    fix_summary += f"- {team_name}:\n" + "\n".join(stats_lines) + "\n"
            else:
                fix_summary += "Match Stats: Not available\n"

        # H2H
        h2h = await get_h2h_by_sport(h2h=f"{home_id}-{away_id}", sport=fix["sport"])
        if h2h:
            fix_summary += "\nLast 5 Head-to-Head:\n"
            for h in h2h:
                h_name = h["home_name"]
                a_name = h["away_name"]
                gh = h["goals"]["home"]
                ga = h["goals"]["away"]
                fix_summary += f"- {h_name} {gh} - {ga} {a_name}\n"
        else:
            fix_summary += "H2H: Not available\n"

        # LAST 5
        last_5_home = await get_last_matches_by_sport(
            team_id=home_id, sport=fix["sport"], season=season
        )
        last_5_away = await get_last_matches_by_sport(
            team_id=away_id, sport=fix["sport"], season=season
        )
        fix_summary += f"\n{home_name} Last 5: {format_last_matches(matches=last_5_home, team_id=home_id, sport=fix['sport'])}\n"
        fix_summary += f"{away_name} Last 5: {format_last_matches(matches=last_5_away, team_id=away_id, sport=fix['sport'])}\n"

        summary += fix_summary + "=" * 60 + "\n"

    return summary or "No matches found."


async def generate_multimatch_coupon(fixtures_summary: str, odds: float):
    json_format = (
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
    )

    odds = (
        f"{odds} total odds"
        if not isinstance(odds, list)
        else (
            f"Football total odds: {odds[0]}\n"
            f"Basketball total odds: {odds[1]}\n"
            f"American Football total odds: {odds[2]}\n"
            f"Hockey total odds: {odds[3]}\n"
        )
    )

    prompt = (
        "You are a sports betting analyst.\n\n"
        f"Based ONLY on the statistical summaries below, generate three combo bets (accumulators), each containing one selection from EVERY listed match, to reach approximately:\n"
        f"{odds}.\n\n"
        "For each combo:\n"
        "- Low Risk: Use the safest data-supported selections. If you cannot reach the requested odds with only low-risk choices, carefully increase risk (explain why).\n"
        "- Medium Risk: Moderately ambitious, but still justified by the stats.\n"
        "- High Risk: High-odds choices, always with logic from the stats.\n\n"
        "DO NOT use any matches, markets, or information outside what is provided.\n\n"
        "Matches:\n"
        f"{fixtures_summary}\n\n"
        "Return RAW JSON only in this format (no code blocks, no extra text):\n"
        f"{json_format}\n\n"
        "Then after --- send a user-friendly English markdown summary with explanations for each pick based on the stats."
    )

    resp = await openai.chat.completions.create(
        model=Config.GPT_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
    )
    content = resp.choices[0].message.content.strip()
    # response = await openai.responses.create(
    #     model="o3-pro",
    #     input=[
    #         {
    #             "role": "user",
    #             "content": prompt,
    #         }
    #     ],
    #     temperature=0.7,
    # )
    # content = resp.output_text
    if "```json" in content:
        json_part = content.split("```json")[1].split("```")[0].strip()
    else:
        json_part = content.split("---")[0].strip()
    coupon = json.loads(r"{}".format(json_part))

    md_part = ""
    if "---" in content:
        md_part = content.split("---", 1)[1].strip()
    elif "```" in content:
        after_json = content.split("`")[-1].strip()
        if after_json:
            md_part = after_json

    return coupon, md_part


async def parse_user_request(matches_text: str = None, league: str = None):
    if matches_text:
        prompt = (
            "لديك المباريات التالية:\n"
            f"'{matches_text}'\n\n"
            "المطلوب:\n"
            "استخرج أسماء المباريات بشكل موحد بالانجليزية: 'الفريق الأول vs الفريق الثاني'.\n"
            "أجب بوضوح مع قابلية تحويل الإجابة إلى json كالتالي:\n"
            """
            [
                {
                    "title": "...",
                    "sport": "..."
                }
            ]
            """
        )
    elif league:
        prompt = (
            "لديك اسم البطولة التالي:\n"
            f"'{league}'\n\n"
            "المطلوب:\n"
            "أعد كتابة اسم البطولة بشكل صحيح بالانجليزية\n"
            "أجب بوضوح مع قابلية تحويل الإجابة إلى json كالتالي:\n"
            """
            {
                "league_name": "..."
            }
            """
        )

    response = await openai.chat.completions.create(
        model=Config.GPT_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )
    content = response.choices[0].message.content
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    result = json.loads(content)
    return result
