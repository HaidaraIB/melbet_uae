from telegram import InlineKeyboardButton
from Config import Config
from client.client_calls.common import openai
from common.lang_dicts import *
from user.buy_voucher.constants import *
from user.analyze_game.api_calls import (
    get_fixture_odds_by_sport,
    get_h2h_by_sport,
    get_team_statistics_by_sport,
    get_team_standing_by_sport,
    get_last_matches_by_sport,
)
from user.buy_voucher.api_calls import get_fixture_stats
from user.buy_voucher.functions import (
    format_basketball_stats,
    format_american_football_stats,
    format_hockey_stats,
    format_football_stats,
    format_last_matches,
    structure_team_standing,
)
import json
import models
import logging

log = logging.getLogger(__name__)


def build_preferences_keyboard(lang: str):
    return [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["choose_pref_for_me"],
                callback_data="choose_pref_for_me",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["choose_pref_sport"],
                callback_data="choose_pref_sport",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["choose_pref_matches"],
                callback_data="choose_pref_matches",
            )
        ],
    ]


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
        if odds:
            fix_summary += "\nOdds:\n"
            printed = set()
            for provider in odds:
                for book in provider.get("bookmakers", []):
                    for market in book.get("bets", []):
                        name = market.get("name")
                        if name not in printed:
                            printed.add(name)
                            values = " | ".join(
                                f"{v['value']}: {v['odd']}" for v in market["values"]
                            )
                            fix_summary += f"- {name}: {values}\n"
        else:
            fix_summary += "- Odds not available\n"

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


def build_get_voucher_confirmation_keyboard(
    user_id: int,
    lang: models.Language,
    odds: int,
):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["confirm_payment"],
                callback_data="confirm_payment",
            ),
            InlineKeyboardButton(
                text=BUTTONS[lang]["cancel_voucher"],
                callback_data="cancel_voucher",
            ),
        ],
    ]
    with models.session_scope() as s:
        user = s.query(models.User).filter_by(user_id=user_id).first()
        subscriptions = (
            s.query(models.Subscription)
            .filter_by(user_id=user_id)
            .order_by(models.Subscription.created_at.desc())
            .all()
        )
        current_sub = subscriptions[0]
        if user.plan_code and user.plan_code != "capital_management":
            if current_sub.status == "active":
                current_plan: models.Plan = current_sub.plan
                sub_id = None
                # first check if previous_sub can fullfill this voucher
                if len(subscriptions) > 1:
                    previous_sub = subscriptions[1]
                    previous_plan: models.Plan = previous_sub.plan
                    if (
                        (
                            previous_plan.code == "plus"
                            and previous_sub.remaining_vouchers
                            >= int(0.2 * previous_plan.vouchers)
                        )
                        or (
                            previous_plan.code == "pro"
                            and previous_sub.remaining_vouchers > 0
                        )
                    ) and odds <= previous_plan.max_odds:
                        sub_id = previous_sub.id
                    elif (
                        current_sub.remaining_vouchers > 0
                        and odds <= current_plan.max_odds
                    ):
                        sub_id = current_sub.id
                elif (
                    current_sub.remaining_vouchers > 0 and odds <= current_plan.max_odds
                ):
                    sub_id = current_sub.id
                if sub_id is not None:
                    keyboard.insert(
                        0,
                        [
                            InlineKeyboardButton(
                                text=BUTTONS[lang]["use_sub"],
                                callback_data=f"use_sub_{sub_id}",
                            )
                        ],
                    )

    return keyboard


# def summarize_fixtures_with_odds_stats(fixtures: list, session: Session) -> str:
#     summary = ""
#     for fix in fixtures:
#         fix_summary = ""
#         fixture_id = fix["fixture"]["id"]
#         home = fix["teams"]["home"]
#         away = fix["teams"]["away"]
#         league = fix["league"]
#         date = fix["fixture"]["date"][:16].replace("T", " ")
#         fix_summary += (
#             f"\n=== {home['name']} vs {away['name']} | {league['name']} | {date} ===\n"
#         )

#         # STANDINGS - From cache
#         try:
#             cached_standings = (
#                 session.query(models.CachedStandings)
#                 .filter_by(league_id=league["id"], season=league["season"])
#                 .first()
#             )

#             if cached_standings:
#                 standings = cached_standings.data
#                 home_stand = next(t for t in standings if t["team"]["id"] == home["id"])
#                 away_stand = next(t for t in standings if t["team"]["id"] == away["id"])
#                 fix_summary += "Standings:\n"
#                 fix_summary += f"- {home['name']}: Rank {home_stand['rank']} | {home_stand['points']} pts\n"
#                 fix_summary += f"- {away['name']}: Rank {away_stand['rank']} | {away_stand['points']} pts\n"
#             else:
#                 fix_summary += "Standings: Not available\n"
#         except Exception as e:
#             standings_error = "Standings: Error loading\n"
#             log.error(f"{standings_error}: {e}")
#             fix_summary += standings_error

#         # ODDS - From cache
#         try:
#             cached_odds = (
#                 session.query(models.CachedOdds)
#                 .filter_by(fixture_id=fixture_id)
#                 .first()
#             )
#             fix_summary += "\nOdds:\n"

#             if cached_odds:
#                 odds_data = cached_odds.data
#                 printed = set()
#                 for provider in odds_data:
#                     for book in provider.get("bookmakers", []):
#                         for market in book.get("bets", []):
#                             name = market.get("name")
#                             if name not in printed:
#                                 printed.add(name)
#                                 values = " | ".join(
#                                     f"{v['value']}: {v['odd']}"
#                                     for v in market["values"]
#                                 )
#                                 fix_summary += f"- {name}: {values}\n"
#                 if not printed:
#                     fix_summary += "- Odds available but no matching markets found\n"
#             else:
#                 fix_summary += "- Odds not available\n"
#         except Exception as e:
#             log.error(f"Error loading odds: {e}")
#             fix_summary += "- Error loading odds\n"

#         # TEAM STATS - From cache
#         try:
#             home_stats = (
#                 session.query(models.CachedTeamStats)
#                 .filter_by(
#                     team_id=home["id"],
#                     league_id=league["id"],
#                     season=league["season"],
#                 )
#                 .first()
#             )

#             away_stats = (
#                 session.query(models.CachedTeamStats)
#                 .filter_by(
#                     team_id=away["id"],
#                     league_id=league["id"],
#                     season=league["season"],
#                 )
#                 .first()
#             )

#             def team_stats_block(stats, label):
#                 if not stats:
#                     return f"{label} Stats: Not available\n"
#                 return (
#                     f"{label} Stats:\n"
#                     f"- Goals For: {stats.data['goals']['for']['average']['total']}\n"
#                     f"- Goals Against: {stats.data['goals']['against']['average']['total']}\n"
#                     f"- Clean Sheets: {stats.data['clean_sheet']['total']}\n"
#                     f"- Failed to Score: {stats.data['failed_to_score']['total']}\n"
#                     f"- BTTS %: {stats.data['both_teams_to_score']['percentage'] if stats.data.get('both_teams_to_score', None) else None}\n"
#                 )

#             fix_summary += (
#                 "\n"
#                 + team_stats_block(home_stats, home["name"])
#                 + team_stats_block(away_stats, away["name"])
#             )
#         except Exception as e:
#             stats_error = "Stats: Error loading"
#             log.error(f"{stats_error}: {e}")
#             fix_summary += f"\n{stats_error}\n"

#         # FIXTURE STATS - From cache
#         try:
#             cached_stats = (
#                 session.query(models.CachedStats)
#                 .filter_by(fixture_id=fixture_id)
#                 .first()
#             )
#             if cached_stats:
#                 fixture_stats = cached_stats.data
#                 fix_summary += "Match Stats:\n"
#                 for team_stats in fixture_stats:
#                     team_name = team_stats["team"]["name"]
#                     stats_lines = [
#                         f"  • {s['type']}: {s['value']}"
#                         for s in team_stats.get("statistics", [])[:5]
#                     ]
#                     fix_summary += f"- {team_name}:\n" + "\n".join(stats_lines) + "\n"
#             else:
#                 fix_summary += "Match Stats: Not available\n"
#         except Exception as e:
#             match_stats_error = "Match Stats: Error loading"
#             log.error(f"{match_stats_error}: {e}")
#             fix_summary += f"{match_stats_error}\n"

#         # H2H - From cache
#         try:
#             cached_h2h = (
#                 session.query(models.CachedH2H)
#                 .filter_by(home_id=home["id"], away_id=away["id"])
#                 .order_by(models.CachedH2H.last_updated.desc())
#                 .first()
#             )

#             if cached_h2h:
#                 h2h = cached_h2h.data
#                 fix_summary += "Last 5 Head-to-Head:\n"
#                 for h in h2h[:5]:
#                     h_name = h["teams"]["home"]["name"]
#                     a_name = h["teams"]["away"]["name"]
#                     gh = h["goals"]["home"]
#                     ga = h["goals"]["away"]
#                     fix_summary += f"- {h_name} {gh} - {ga} {a_name}\n"
#             else:
#                 fix_summary += "H2H: Not available\n"
#         except Exception as e:
#             h2h_error = "H2H: Error loading"
#             log.error(f"{h2h_error}: {e}")
#             fix_summary += f"{h2h_error}\n"

#         # FORM - From cached team results
#         try:

#             def form_block(team_id: int, label: str) -> str:
#                 # Get cached results for the team
#                 cached_results = (
#                     session.query(models.CachedTeamResults)
#                     .filter_by(team_id=team_id)
#                     .first()
#                 )

#                 if not cached_results or not cached_results.data:
#                     return f"{label} Last 5: Not available\n"

#                 results = []
#                 for m in cached_results.data[:5]:  # Get last 5 matches
#                     is_home = m["teams"]["home"]["id"] == team_id
#                     goals_for = m["goals"]["home"] if is_home else m["goals"]["away"]
#                     goals_against = (
#                         m["goals"]["away"] if is_home else m["goals"]["home"]
#                     )
#                     venue = "H" if is_home else "A"  # H = Home, A = Away
#                     outcome = (
#                         "W"
#                         if goals_for > goals_against
#                         else "D" if goals_for == goals_against else "L"
#                     )
#                     results.append(f"{venue} {goals_for}-{goals_against} ({outcome})")
#                 return f"{label} Last 5: " + " | ".join(results) + "\n"

#             # Get form for both teams
#             fix_summary += form_block(home["id"], home["name"])
#             fix_summary += form_block(away["id"], away["name"])

#             def format_last_match_stats(label: str, team_id: int) -> str:
#                 # Get cached results for the team
#                 cached_results = (
#                     session.query(models.CachedTeamResults)
#                     .filter_by(team_id=team_id)
#                     .first()
#                 )

#                 if not cached_results or not cached_results.data:
#                     return f"{label} Last 5 Match Stats: Not available\n"

#                 text = f"{label} Last 5 Match Stats:\n"
#                 for match in cached_results.data[:5]:  # Get last 5 matches
#                     # Get stats for this match if available
#                     match_stats = (
#                         session.query(models.CachedStats)
#                         .filter_by(fixture_id=match["fixture"]["id"])
#                         .first()
#                     )

#                     if not match_stats:
#                         continue

#                     # Find this team's stats in the match
#                     team_stats = next(
#                         (ts for ts in match_stats.data if ts["team"]["id"] == team_id),
#                         None,
#                     )

#                     if not team_stats:
#                         continue

#                     # Format the stats
#                     opponent = (
#                         match["teams"]["away"]["name"]
#                         if match["teams"]["home"]["id"] == team_id
#                         else match["teams"]["home"]["name"]
#                     )
#                     date = match["fixture"]["date"][:10]

#                     text += f"- vs {opponent} ({date}):\n"
#                     for stat in team_stats.get("statistics", []):
#                         text += f"  • {stat['type']}: {stat['value']}\n"

#                 return (
#                     text
#                     if text.count("\n") > 1
#                     else f"{label} Last 5 Match Stats: No detailed stats available\n"
#                 )

#             # Get detailed stats for both teams
#             fix_summary += format_last_match_stats(home["name"], home["id"])
#             fix_summary += format_last_match_stats(away["name"], away["id"])

#         except Exception as e:
#             recent_form_error = "Recent form: Error loading"
#             log.error(f"{recent_form_error}: {e}")
#             fix_summary += f"{recent_form_error}\n"

#         def is_match_data_complete(match: str) -> bool:
#             # has_standings = "Rank" in match or "points" in match
#             # has_match_stats = (
#             #     "Fouls" in match or "Total Corners" in match or "Yellow Cards" in match
#             # )
#             has_team_stats = "Goals For" in match or "Clean Sheets" in match
#             has_form = "Last 5" in match
#             has_odds = any(v in match for v in MARKETS_NEEDED.values())
#             return has_team_stats and has_form and has_odds

#         if is_match_data_complete(fix_summary):
#             summary += fix_summary + "=" * 60 + "\n"

#     return summary or "No matches found."
