import requests
import openai
from Config import Config
from utils.api_calls import HEADERS, BASE_URL
from client.client_calls.common import openai
from common.constants import TIMEZONE_NAME
from datetime import datetime
import random

LEAGUE_MAP = {
    # Spain (La Liga) - ID: 140
    "la liga": 140,
    "laliga": 140,
    "الدوري الإسباني": 140,
    "ليغا": 140,
    "دوري الدرجة الأولى الإسباني": 140,
    "primera división": 140,
    "اسبانيا": 140,  # Country fallback
    "إسبانيا": 140,
    # England (Premier League) - ID: 39
    "premier league": 39,
    "البريميرليغ": 39,
    "الدوري الإنجليزي الممتاز": 39,
    "epl": 39,
    "barclays premier league": 39,
    "انجلترا": 39,  # Country fallback
    "إنجلترا": 39,
    # Italy (Serie A) - ID: 135
    "serie a": 135,
    "سيريا أ": 135,
    "الدوري الإيطالي": 135,
    "الدوري الإيطالي الممتاز": 135,
    "ايطاليا": 135,  # Country fallback
    "إيطاليا": 135,
    # Germany (Bundesliga) - ID: 78
    "bundesliga": 78,
    "بوندسليغا": 78,
    "الدوري الألماني": 78,
    "bundesliga 1": 78,
    "المانيا": 78,  # Country fallback
    "ألمانيا": 78,
    # France (Ligue 1) - ID: 61
    "ligue 1": 61,
    "ليغ 1": 61,
    "الدوري الفرنسي": 61,
    "ليغ 1 الفرنسي": 61,
    "فرنسا": 61,  # Country fallback
    # UEFA Competitions
    "champions league": 2,
    "دوري الأبطال": 2,
    "ucl": 2,
    "uefa champions league": 2,
    "دوري أبطال أوروبا": 2,
    "europa league": 3,
    "الدوري الأوروبي": 3,
    "uel": 3,
    "uefa europa league": 3,
    "الدوري الأوروبي لكرة القدم": 3,
    "europa conference league": 848,
    "الدوري الأوروبي المؤتمر": 848,
    "uefa europa conference league": 848,
    "uecl": 848,
    "دوري المؤتمر الأوروبي": 848,
    # Other Major Leagues
    "mls": 253,
    "الدوري الأمريكي": 253,
    "major league soccer": 253,
    "الدوري الأمريكي لكرة القدم": 253,
    "usa": 253,  # Country fallback
    "brasileirao": 71,
    "الدوري البرازيلي": 71,
    "brasileirão série a": 71,
    "campeonato brasileiro": 71,
    "brazil": 71,  # Country fallback
    "البرازيل": 71,
    "eredivisie": 88,
    "الدوري الهولندي": 88,
    "eredivisie holland": 88,
    "netherlands": 88,  # Country fallback
    "هولندا": 88,
    "primeira liga": 94,
    "الدوري البرتغالي": 94,
    "liga portugal": 94,
    "portugal": 94,  # Country fallback
    "البرتغال": 94,
    "super lig": 203,
    "الدوري التركي": 203,
    "سوبر ليغ": 203,
    "تركيا": 203,  # Country fallback
    "الدوري التركي الممتاز": 203,
    "belgian pro league": 144,
    "الدوري البلجيكي": 144,
    "jupiler pro league": 144,
    "بلجيكا": 144,  # Country fallback
    "دوري بلجيكا الممتاز": 144,
    "scottish premiership": 179,
    "الدوري الاسكتلندي": 179,
    "premiership scotland": 179,
    "اسكتلندا": 179,  # Country fallback
    "الدوري الاسكتلندي الممتاز": 179,
    "austrian bundesliga": 218,
    "الدوري النمساوي": 218,
    "بوندسليغا النمسا": 218,
    "النمسا": 218,  # Country fallback
    "دوري النمسا الممتاز": 218,
    # Domestic Cups
    "copa del rey": 143,
    "كأس الملك": 143,
    "كأس إسبانيا": 143,
    "copa de españa": 143,
    "fa cup": 45,
    "كأس الاتحاد الإنجليزي": 45,
    "كأس إنجلترا": 45,
    "كأس الاتحاد": 45,
    "dfb pokal": 81,
    "كأس ألمانيا": 81,
    "كأس الاتحاد الألماني": 81,
    "coppa italia": 137,
    "كأس إيطاليا": 137,
    "كأس ايطاليا": 137,
    "coupe de france": 66,
    "كأس فرنسا": 66,
    "كأس الاتحاد الفرنسي": 66,
    # South American Competitions
    "copa libertadores": 13,
    "كأس ليبرتادوريس": 13,
    "كأس المحررين": 13,
    "copa sudamericana": 15,
    "كأس سود أمريكانا": 15,
    "كأس أمريكا الجنوبية": 15,
}

TEAM_MAP = {
    # La Liga
    "barcelona": 529,
    "برشلونة": 529,
    "fc barcelona": 529,
    "real madrid": 541,
    "ريال مدريد": 541,
    "atletico madrid": 530,
    "أتلتيكو مدريد": 530,
    "valencia": 532,
    "فالنسيا": 532,
    "sevilla": 536,
    "اشبيلية": 536,
    # Premier League
    "liverpool": 40,
    "ليفربول": 40,
    "manchester united": 33,
    "مانشستر يونايتد": 33,
    "manchester city": 50,
    "مانشستر سيتي": 50,
    "arsenal": 42,
    "آرسنال": 42,
    "chelsea": 49,
    "تشيلسي": 49,
    "tottenham": 47,
    "توتنهام": 47,
    # Serie A
    "juventus": 496,
    "يوفنتوس": 496,
    "inter milan": 505,
    "إنتر ميلان": 505,
    "ac milan": 489,
    "إيه سي ميلان": 489,
    "roma": 497,
    "روما": 497,
    "napoli": 492,
    "نابولي": 492,
    # Bundesliga
    "bayern munich": 157,
    "بايرن ميونخ": 157,
    "dortmund": 165,
    "دورتموند": 165,
    "rb leipzig": 173,
    "آر بي لايبزيغ": 173,
}


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


def get_fixtures(
    league_id: int,
    team_id: int,
    from_date: datetime,
    to_date: datetime,
):
    if not league_id:
        for l_id in list(set(LEAGUE_MAP.values())):
            for season in (from_date.year, from_date.year -1):
                url = f"{BASE_URL}/fixtures"
                params = {
                    "from": from_date.strftime("%Y-%m-%d"),
                    "to": to_date.strftime("%Y-%m-%d"),
                    "season": season,
                    "timezone": TIMEZONE_NAME,
                    "league": l_id
                }
                if team_id:
                    params["team"] = team_id

                r = requests.get(url, params=params, headers=HEADERS)
                data = r.json()
                if data.get("response", []):
                    break
            if data.get("response", []):
                break
    else:
        for season in (from_date.year, from_date.year -1):
            url = f"{BASE_URL}/fixtures"
            params = {
                "from": from_date.strftime("%Y-%m-%d"),
                "to": to_date.strftime("%Y-%m-%d"),
                "season": season,
                "timezone": TIMEZONE_NAME,
                "league": league_id
            }
            if team_id:
                params["team"] = team_id

            r = requests.get(url, params=params, headers=HEADERS)
            data = r.json()
            if data.get("response", []):
                break
    return data.get("response", [])


def get_fixture_odds(fixture_id: int):
    url = f"{BASE_URL}/odds"
    params = {"fixture": fixture_id}
    r = requests.get(url, params=params, headers=HEADERS)
    data = r.json()
    return data.get("response", [])


def get_fixture_stats(fixture_id: int):
    url = f"{BASE_URL}/fixtures/statistics"
    params = {"fixture": fixture_id}
    r = requests.get(url, params=params, headers=HEADERS, timeout=20)
    data = r.json()
    return data.get("response", [])


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
        model=Config.GPT_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )
    return response.choices[0].message.content
