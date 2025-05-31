from Config import Config
from client.client_calls.common import openai
from telegram import InlineKeyboardButton
import models
from common.lang_dicts import *


def summarize_matches(matches: list[dict]):
    summary = []
    for m in matches:
        summary.append(
            f"{m['home_name']} {m['goals']['home']} - {m['goals']['away']} {m['away_name']} on {m['date']}"
        )
    return "\n".join(summary)


def summarize_injuries(injuries: list[dict], sport: str):
    if not injuries:
        return
    if sport == "football":
        return "\n".join(
            [
                f"{i['player']['name']} ({i['player']['type']}) - {i['player']['reason']}"
                for i in injuries
            ]
        )
    if sport == "american_football":
        return "\n".join(
            [
                f"{i['player']['name']} ({i['status']}) - {i['description']}"
                for i in injuries
            ]
        )


def summarize_odds(odds: list[dict]):
    summaries = []
    printed = set()
    for book in odds:
        for bet in book.get("bookmakers", []):
            for market in bet.get("bets", []):
                name = market.get("name", "")
                if name not in printed:
                    printed.add(name)
                    outcomes = [
                        f"{o['value']}: {o['odd']}" for o in market.get("values", [])
                    ]
                    summaries.append(f"{name}:\n{" | ".join(outcomes)}\n\n")
    result = "\n".join(summaries)
    return result


async def generate_gpt_analysis(match_info: dict):
    prompt = (
        "You are a professional football analyst.\n\n"
        "Based on the match data below, generate exactly 3 smart betting suggestions, classified by risk level.\n\n"
        "Each suggestion must include:\n"
        "- Title (e.g. Barcelona to Win)\n"
        "- Market Type (e.g. 1X2, BTTS, Over 2.5)\n"
        "- Risk Level (Low, Medium, High)\n"
        "- Estimated Probability (in %)\n"
        "- Actual Market Odds (from bookmakers)\n"
        "- Value assessment: compare your probability with implied odds\n"
        "- Reason (max 3 lines)\n\n"
        "Then provide the following additional sections:\n"
        "4. Optional Combo Bet (only if 2+ suggestions align logically). Include combined odds and brief reasoning.\n"
        "5. One 'Avoid this Bet' suggestion (a market that looks risky or overestimated)\n"
        "6. Value Indicator for each bet: ✅ (Value), ⚠️ (Fair), ❌ (No value)\n"
        "7. Recap Summary Table:\n"
        "- Best Value Bet\n"
        "- Safest Bet\n"
        "- Highest Payout Potential\n\n"
        "Match Summary:\n"
        f"- Teams: {match_info['teams']}\n"
        f"- Date: {match_info['date']}\n"
        f"- League: {match_info['league']}\n"
        f"- Venue: {match_info['venue']}\n\n"
        f"Bookmaker Odds:\n{match_info['odds']}\n\n"
        f"Last 5 Head-to-Head Matches:\n{match_info['h2h']}\n\n"
        f"Last 5 Matches:\n"
        f"{match_info['home_name']}:\n{match_info['home_last']}\n"
        f"{match_info['away_name']}:\n{match_info['away_last']}\n\n"
        f"Standings:\n"
        f"{match_info['home_name']}: {match_info['home_rank']}\n"
        f"{match_info['away_name']}: {match_info['away_rank']}\n\n"
        f"Injuries:\n"
        f"{match_info['home_name']}:\n{match_info['home_inj']}\n"
        f"{match_info['away_name']}:\n{match_info['away_inj']}\n\n"
        "Output Format:\n"
        "- Use English and Telegram Markdown formatting\n"
        "- Use 🔹 / 🔸 / 🔺 icons for Low / Medium / High risk\n"
        "- Bold the suggestion titles\n"
        "- Use bullet points for: Market, Probability, Odds, Value, Reason\n"
    )

    response = await openai.chat.completions.create(
        model=Config.GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def build_matches_keyboard(matches: list[dict], lang, page=0, per_page=5):
    start = page * per_page
    end = start + per_page
    sliced = matches[start:end]

    keyboard = []
    for match in sliced:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{match['home_name']} vs {match['away_name']}",
                    callback_data=f"analyze_match_{match['fixture_id']}",
                )
            ]
        )

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text=BUTTONS[lang]["prev"],
                callback_data=f"analyze_match_page_{page-1}",
            )
        )
    if end < len(matches):
        nav_buttons.append(
            InlineKeyboardButton(
                text=BUTTONS[lang]["next"],
                callback_data=f"analyze_match_page_{page+1}",
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)
    return keyboard


async def ask_gpt_about_match(teams: str, sport: str):
    prompt = f"In {sport} extract clearly from {teams} the two team names in lower case English letters. the priority is for the most famous teams. Return as JSON with: team1, team2 "
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
    return response.choices[0].message.content.replace("json", "").replace("```", "")


def build_sports_keyboard(lang: models.Language):
    return [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["football"],
                callback_data="analyze_football",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["basketball"],
                callback_data="analyze_basketball",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["american_football"],
                callback_data="analyze_american_football",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["hockey"],
                callback_data="analyze_hockey",
            )
        ],
    ]
