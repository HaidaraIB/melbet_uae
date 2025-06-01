from models import Language

LANGUAGES = {
    "ar": "العربية",
    "en": "English",
    "sp": "Spanish",
    "pt": "Portuguese",
}

DIALECTS = {
    "ar": {
        "msa": "عربي فصحى",
        "eg": "مصري",
        "sy": "سوري",
        "sa": "سعودي",
        "ma": "مغربي",
    },
    "en": {
        "am": "American",
        "br": "British",
        "ind": "Indian",
        "sing": "Singaporean",
        "jam": "Jamaican",
        "nig": "Nigerian",
        "aus": "Australian",
    },
    "sp": {
        "cast": "Castilian",
        "and": "Andalusian",
        "muc": "Murcian",
        "lat": "Llanito",
        "cat": "Catalan",
        "bas": "Basque",
    },
    "pt": {
        "pt": "European Portuguese",
        "br": "Brazilian Portuguese",
        "ao": "Angolan Portuguese",
        "mz": "Mozambican Portuguese",
        "gw": "Guinean Portuguese",
        "st": "São Toméan Portuguese",
        "cv": "Cape Verdean Portuguese",
    },
}
SPORTS = {
    "football": {
        Language.ARABIC: "⚽️ كرة القدم",
        Language.ENGLISH: "Football ⚽️",
    },
    "basketball": {
        Language.ARABIC: "🏀 كرة السلة",
        Language.ENGLISH: "Basketball 🏀",
    },
    "hockey": {
        Language.ARABIC: "🏒 هوكي",
        Language.ENGLISH: "Hockey 🏒",
    },
    "american football": {
        Language.ARABIC: "🏈 كرة القدم الأميريكية",
        Language.ENGLISH: "American Football 🏈",
    },
}
LEAGUES = {
    "football": {
        "premier_league": {
            "name": "Premier League",
            "country": "England",
            "id": 39,
        },
        "la_liga": {
            "name": "La Liga",
            "country": "Spain",
            "id": 140,
        },
        "bundesliga": {
            "name": "Bundesliga",
            "country": "Germany",
            "id": 78,
        },
        "serie_a": {
            "name": "Serie A",
            "country": "Italy",
            "id": 135,
        },
        "ligue_1": {
            "name": "Ligue 1",
            "country": "France",
            "id": 61,
        },
        "champions_league": {
            "name": "UEFA Champions League",
            "country": "Europe",
            "id": 2,
        },
        "europa_league": {
            "name": "UEFA Europa League",
            "country": "Europe",
            "id": 3,
        },
        "europa_conference": {
            "name": "UEFA Europa Conference League",
            "country": "Europe",
            "id": 848,
        },
        "caf_champions_league": {
            "name": "CAF Champions League",
            "country": "Africa",
            "id": 2001,
        },
        "mls": {
            "name": "Major League Soccer",
            "country": "USA",
            "id": 253,
        },
        "brasileirao": {
            "name": "Brasileirão Série A",
            "country": "Brazil",
            "id": 71,
        },
        "eredivisie": {
            "name": "Eredivisie",
            "country": "Netherlands",
            "id": 88,
        },
        "primeira_liga": {
            "name": "Primeira Liga",
            "country": "Portugal",
            "id": 94,
        },
        "saudi_pro": {
            "name": "Saudi Pro League",
            "country": "Saudi Arabia",
            "id": 307,
        },
        "libertadores": {
            "name": "Copa Libertadores",
            "country": "South America",
            "id": 13,
        },
        "sudamericana": {
            "name": "Copa Sudamericana",
            "country": "South America",
            "id": 15,
        },
        "fa_cup": {
            "name": "FA Cup",
            "country": "England",
            "id": 45,
        },
        "efl_cup": {
            "name": "EFL Cup (Carabao Cup)",
            "country": "England",
            "id": 46,
        },
        "dfb_pokal": {
            "name": "DFB-Pokal",
            "country": "Germany",
            "id": 81,
        },
        "copa_del_rey": {
            "name": "Copa del Rey",
            "country": "Spain",
            "id": 143,
        },
        "coppa_italia": {
            "name": "Coppa Italia",
            "country": "Italy",
            "id": 137,
        },
        "coupe_de_france": {
            "name": "Coupe de France",
            "country": "France",
            "id": 66,
        },
        "turkish_super_lig": {
            "name": "Süper Lig",
            "country": "Turkey",
            "id": 203,
        },
        "egyptian_premier_league": {
            "name": "Egyptian Premier League",
            "country": "Egypt",
            "id": 233,
        },
        "botola_pro": {
            "name": "Botola Pro",
            "country": "Morocco",
            "id": 200,
        },
    },
    "basketball": {
        "nba": {
            "name": "NBA",
            "country": "USA",
            "id": 12,
        },
        "euroleague": {
            "name": "EuroLeague",
            "country": "Europe",
            "id": 285,
        },
        "acb": {
            "name": "Liga ACB",
            "country": "Spain",
            "id": 293,
        },
        "aba_league": {
            "name": "ABA League",
            "country": "Adriatic",
            "id": 298,
        },
        "vtb_united": {
            "name": "VTB United League",
            "country": "Russia/Eastern Europe",
            "id": 295,
        },
        "turkish_super_league": {
            "name": "Turkish Basketball Super League",
            "country": "Turkey",
            "id": 297,
        },
        "italian_legabasket": {
            "name": "Lega Basket Serie A",
            "country": "Italy",
            "id": 294,
        },
        "greek_basket_league": {
            "name": "Greek Basket League",
            "country": "Greece",
            "id": 296,
        },
    },
    "tennis": {
        "atp_wimbledon": {
            "name": "ATP Wimbledon",
            "country": "UK",
            "id": 540,
        },
        "atp_roland_garros": {
            "name": "ATP Roland Garros",
            "country": "France",
            "id": 541,
        },
        "atp_us_open": {
            "name": "ATP US Open",
            "country": "USA",
            "id": 542,
        },
        "atp_australian_open": {
            "name": "ATP Australian Open",
            "country": "Australia",
            "id": 543,
        },
        "atp_masters": {
            "name": "ATP Masters 1000",
            "country": "World",
            "id": 544,
        },
    },
    "hockey": {
        "nhl": {
            "name": "NHL",
            "country": "USA/Canada",
            "id": 52,
        },
        "khl": {
            "name": "KHL",
            "country": "Russia/Eastern Europe",
            "id": 53,
        },
        "shl": {
            "name": "SHL",
            "country": "Sweden",
            "id": 54,
        },
        "liiga": {
            "name": "Liiga",
            "country": "Finland",
            "id": 55,
        },
    },
    "american football": {
        "nfl": {
            "name": "NFL",
            "country": "USA",
            "id": 1,
        },
        "ncaa": {
            "name": "NCAA Football",
            "country": "USA",
            "id": 2,
        },
        "cfl": {
            "name": "Canadian Football League",
            "country": "Canada",
            "id": 3,
        },
    },
}
