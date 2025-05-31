from dateutil import tz
from Config import Config

BACK_TO_HOME_PAGE_TEXT = "العودة إلى القائمة الرئيسية 🔙"

HOME_PAGE_TEXT = "القائمة الرئيسية 🔝"

BACK_BUTTON_TEXT = "الرجوع 🔙"


TIMEZONE_NAME = "Asia/Dubai"

TIMEZONE = tz.gettz(TIMEZONE_NAME)

SPORT_API = {
    "football": {
        "host": Config.X_RAPIDAPI_FB_HOST,
        "fixtures_url": f"https://{Config.X_RAPIDAPI_FB_HOST}/v3/fixtures",
        "h2h_url": f"https://{Config.X_RAPIDAPI_FB_HOST}/v3/fixtures/headtohead",
        "team_statistics_url": f"https://{Config.X_RAPIDAPI_FB_HOST}/v3/teams/statistics",
        "team_injuries_url": f"https://{Config.X_RAPIDAPI_FB_HOST}/injuries",
    },
    "basketball": {
        "host": Config.X_RAPIDAPI_BB_HOST,
        "fixtures_url": f"https://{Config.X_RAPIDAPI_BB_HOST}/games",
        "h2h_url": f"https://{Config.X_RAPIDAPI_BB_HOST}/games",
        "team_statistics_url": f"https://{Config.X_RAPIDAPI_BB_HOST}/statistics",
        "team_injuries_url": None,
    },
    "american_football": {
        "host": Config.X_RAPIDAPI_AFB_HOST,
        "fixtures_url": f"https://{Config.X_RAPIDAPI_AFB_HOST}/games",
        "h2h_url": f"https://{Config.X_RAPIDAPI_AFB_HOST}/games",
        "team_statistics_url": None,
        "team_injuries_url": f"https://{Config.X_RAPIDAPI_AFB_HOST}/injuries",
    },
    "hockey": {
        "host": Config.X_RAPIDAPI_H_HOST,
        "fixtures_url": f"https://{Config.X_RAPIDAPI_H_HOST}/games",
        "h2h_url": f"https://{Config.X_RAPIDAPI_H_HOST}/games/h2h",
        "team_statistics_url": f"https://{Config.X_RAPIDAPI_H_HOST}/teams/statistics",
        "team_injuries_url": None,
    },
}
