import requests
import openai
from Config import Config
from utils.api_calls import HEADERS, BASE_URL
from client.client_calls.common import openai
from datetime import datetime

LEAGUE_MAP = {
    "la liga": 140,
    "laliga": 140,
    "اسبانيا": 140,
    "إسبانيا": 140,
    "premier league": 39,
    "انجلترا": 39,
    "إنجلترا": 39,
    "serie a": 135,
    "ايطاليا": 135,
    "إيطاليا": 135,
    "bundesliga": 78,
    "المانيا": 78,
    "ألمانيا": 78,
    "ligue 1": 61,
    "فرنسا": 61,
}
TEAM_MAP = {
    "barcelona": 529,
    "برشلونة": 529,
    "real madrid": 541,
    "ريال مدريد": 541,
    "liverpool": 40,
    "ليفربول": 40,
}
COUNTRY_MAP = {
    "spain": "Spain",
    "اسبانيا": "Spain",
    "إسبانيا": "Spain",
    "england": "England",
    "انجلترا": "England",
    "إنجلترا": "England",
    "germany": "Germany",
    "المانيا": "Germany",
    "ألمانيا": "Germany",
    "france": "France",
    "فرنسا": "France",
}


def extract_ids(preferences: str):
    text = preferences.lower()
    league_id = None
    team_id = None
    country = None

    for key, val in LEAGUE_MAP.items():
        if key in text:
            league_id = val
            break
    for key, val in TEAM_MAP.items():
        if key in text:
            team_id = val
            break
    for key, val in COUNTRY_MAP.items():
        if key in text:
            country = val
            break
    return league_id, team_id, country


def get_fixtures(
    league_id: int,
    team_id: int,
    country: str,
    from_date: datetime,
    to_date: datetime,
):
    url = f"{BASE_URL}/fixtures"
    params = {
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d"),
    }
    if league_id:
        params["league"] = league_id
    if team_id:
        params["team"] = team_id
    if country:
        params["country"] = country

    headers = {
        "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": Config.X_RAPIDAPI_HOST,
    }
    r = requests.get(url, params=params, headers=headers, timeout=20)
    if r.status_code == 200:
        return r.json().get("response", [])
    else:
        return []


def get_fixture_odds(fixture_id: int):
    url = f"{BASE_URL}/odds"
    params = {"fixture": fixture_id}
    headers = {
        "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": Config.X_RAPIDAPI_HOST,
    }
    r = requests.get(url, params=params, headers=headers, timeout=20)
    if r.status_code == 200:
        return r.json().get("response", [])
    return []


def get_fixture_stats(fixture_id: int):
    url = f"{BASE_URL}/fixtures/statistics"
    params = {"fixture": fixture_id}
    headers = {
        "X-RapidAPI-Key": Config.X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": Config.X_RAPIDAPI_HOST,
    }
    r = requests.get(url, params=params, headers=headers, timeout=20)
    if r.status_code == 200:
        return r.json().get("response", [])
    return []


def summarize_fixtures_with_odds_stats(fixtures: dict, max_count=6):
    summary = ""
    for fix in fixtures[:max_count]:
        fixture_id = fix["fixture"]["id"]
        teams = fix["teams"]["home"]["name"] + " vs " + fix["teams"]["away"]["name"]
        date = fix["fixture"]["date"][:16].replace("T", " ")
        league = fix["league"]["name"]

        # جلب odds (اختصار لأهم الأسواق)
        odds_list = get_fixture_odds(fixture_id)
        odds_text = ""
        for odds_pack in odds_list:
            for bookmaker in odds_pack.get("bookmakers", []):
                for market in bookmaker.get("bets", []):
                    if market["name"] in ["Match Winner", "1X2"]:
                        values = market.get("values", [])
                        for val in values:
                            odds_text += f'{val["value"]}: {val["odd"]} | '
        odds_text = odds_text.strip(" |")
        # جلب stats (مقتطفات فقط)
        stats_list = get_fixture_stats(fixture_id)
        stats_text = ""
        for stats in stats_list:
            team = stats.get("team", {}).get("name", "")
            stats_pairs = stats.get("statistics", [])[:2]  # خذ أول اثنين فقط اختصاراً
            for s in stats_pairs:
                stats_text += f"{team} {s['type']}: {s['value']} | "

        summary += f"\n{teams} | {league} | {date}\nOdds: {odds_text}\nStats: {stats_text.strip(' |')}\n"
    if not summary:
        summary = "No matches found for your preferences in the selected period.\n"
    return summary


def build_gpt_prompt(user_data: dict, fixtures_summary):
    return (
        "User voucher request:\n"
        f"- Amount: {user_data['amount']} AED\n"
        f"- Desired Odds: {user_data['odds']}\n"
        f"- Duration: {user_data['duration_value']} {user_data['duration_type']}\n"
        f"- Preferences: {user_data['preferences']}\n\n"
        "Available matches during this period (with odds and main stats):\n"
        f"{fixtures_summary}\n\n"
        "Task:\n"
        f"Based on the above, create 3 bet slips for the user with a total odds around {user_data['odds']}:\n"
        "- Low Risk: Most matches, low individual odds, higher probability of winning.\n"
        "- Medium Risk: Fewer matches, higher odds.\n"
        "- High Risk: One or two matches with high odds (higher risk, bigger payout).\n\n"
        "For each slip, explain your selection logic in 2 lines.\n"
        "Summarize the options in a simple table.\n"
        "End your reply with a short, clear summary for the user (in Arabic)."
    )


async def gpt_analyze_bet_slips(prompt: str):
    response = await openai.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


