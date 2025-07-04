from Config import Config


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
        "team_statistics_url": f"https://{Config.X_RAPIDAPI_AFB_HOST}/games/statistics/teams",
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


CTA_LIST = [
    "For deeper tactical breakdowns, unlock your Player account before the next kickoff.",
    "Get your Player account now and never miss exclusive pre-match analysis.",
    "Stay ahead—join Player for expert pre-match insights and tactical angles.",
    "Serious about football? Player gives you the edge with in-depth match analytics.",
]
