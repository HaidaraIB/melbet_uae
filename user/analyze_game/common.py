from Config import Config
from client.client_calls.common import openai
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
    elif sport == "american_football":
        return "\n".join(
            [
                f"{i['player']['name']} ({i['status']}) - {i['description']}"
                for i in injuries
            ]
        )


async def generate_gpt_analysis(match_info: dict):
    prompt = (
        "You are a professional football analyst.\n\n"
        "Based on the match data and ALL available betting markets provided below, generate exactly 3 smart betting suggestions, each from a DIFFERENT market type (for example: 1X2, Asian Handicap, Total Goals, Cards, Corners, Goal Method, Player to Score, etc. — only from the markets present in the data).\n\n"
        "You MUST use a different market for each suggestion. Do NOT repeat any market type in your main picks. Select from the actual markets and odds provided below.\n\n"
        "Each suggestion must include:\n"
        "- Title (e.g., PSG to Win, Over 3.5 Cards, Lautaro Martinez to Score)\n"
        "- Market Type (exactly as it appears in the data)\n"
        "- Risk Level (Low, Medium, High)\n"
        "- Estimated Probability (in %)\n"
        "- Actual Market Odds (from bookmakers)\n"
        "- Value assessment: compare your probability with implied odds, and mark as ✅ (Value), ⚠️ (Fair), or ❌ (No value)\n"
        "- Reason (max 3 lines, based strictly on provided stats and match data)\n\n"
        "Then provide the following additional sections:\n"
        "4. Optional Combo Bet (if at least 2 suggestions logically align). Show combined odds and reasoning.\n"
        "5. One 'Avoid this Bet' suggestion (pick the riskiest or least valuable bet from available markets).\n"
        "6. Value Indicator for each bet: ✅ (Value), ⚠️ (Fair), ❌ (No value)\n"
        "7. Recap Summary Table for this match:\n"
        "   - Best Value Bet\n"
        "   - Safest Bet\n"
        "   - Highest Payout Potential\n\n"
        "STRICT INSTRUCTIONS:\n"
        "- Use ONLY the markets and odds provided below, do NOT invent or generalize.\n"
        "- Each main suggestion must use a different market type (e.g., not three 'Goals Over/Under' bets).\n"
        "- Reasons must cite specific stats, form, or odds from the data provided.\n"
        "- Do NOT use combo bets in the 3 main suggestions.\n"
        "- Format using Telegram Markdown (bullets, bold, icons, etc.).\n\n"
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
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
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
    # return response.output_text


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
