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
        # Top European Leagues
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
        "belgian_pro_league": {
            "name": "Belgian Pro League",
            "country": "Belgium",
            "id": 144,
        },
        "scottish_premiership": {
            "name": "Scottish Premiership",
            "country": "Scotland",
            "id": 179,
        },
        "swiss_super_league": {
            "name": "Swiss Super League",
            "country": "Switzerland",
            "id": 207,
        },
        "austrian_bundesliga": {
            "name": "Austrian Bundesliga",
            "country": "Austria",
            "id": 218,
        },
        "russian_premier_liga": {
            "name": "Russian Premier Liga",
            "country": "Russia",
            "id": 235,
        },
        "ukrainian_premier_liga": {
            "name": "Ukrainian Premier League",
            "country": "Ukraine",
            "id": 333,
        },
        "turkish_super_lig": {
            "name": "Süper Lig",
            "country": "Turkey",
            "id": 203,
        },
        "danish_superliga": {
            "name": "Danish Superliga",
            "country": "Denmark",
            "id": 119,
        },
        "norwegian_eliteserien": {
            "name": "Eliteserien",
            "country": "Norway",
            "id": 103,
        },
        "swedish_allsvenskan": {
            "name": "Allsvenskan",
            "country": "Sweden",
            "id": 113,
        },
        # European Cups
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
        "uefa_super_cup": {
            "name": "UEFA Super Cup",
            "country": "Europe",
            "id": 733,
        },
        # Domestic Cups
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
        "taça_de_portugal": {
            "name": "Taça de Portugal",
            "country": "Portugal",
            "id": 96,
        },
        # International Competitions
        "world_cup": {
            "name": "FIFA World Cup",
            "country": "International",
            "id": 1,
        },
        "euro_qualifiers": {
            "name": "European Championship Qualifiers",
            "country": "Europe",
            "id": 47,
        },
        "euro_championship": {
            "name": "UEFA European Championship",
            "country": "Europe",
            "id": 4,
        },
        "nations_league": {
            "name": "UEFA Nations League",
            "country": "Europe",
            "id": 5,
        },
        "copa_america": {
            "name": "Copa América",
            "country": "South America",
            "id": 9,
        },
        "gold_cup": {
            "name": "CONCACAF Gold Cup",
            "country": "North America",
            "id": 14,
        },
        "afcon": {
            "name": "Africa Cup of Nations",
            "country": "Africa",
            "id": 12,
        },
        "asian_cup": {
            "name": "AFC Asian Cup",
            "country": "Asia",
            "id": 16,
        },
        "world_cup_qualifiers": {
            "name": "FIFA World Cup Qualifiers",
            "country": "International",
            "id": 10,
        },
        "club_world_cup": {
            "name": "FIFA Club World Cup",
            "country": "International",
            "id": 7,
        },
        # Americas
        "mls": {
            "name": "Major League Soccer",
            "country": "USA",
            "id": 253,
        },
        "liga_mx": {
            "name": "Liga MX",
            "country": "Mexico",
            "id": 262,
        },
        "argentine_liga_profesional": {
            "name": "Liga Profesional Argentina",
            "country": "Argentina",
            "id": 128,
        },
        "brasileirao": {
            "name": "Brasileirão Série A",
            "country": "Brazil",
            "id": 71,
        },
        "colombian_liga": {
            "name": "Liga BetPlay Dimayor",
            "country": "Colombia",
            "id": 239,
        },
        "chilean_primera": {
            "name": "Primera División de Chile",
            "country": "Chile",
            "id": 265,
        },
        "peruvian_liga": {
            "name": "Liga 1",
            "country": "Peru",
            "id": 284,
        },
        "ecuadorian_liga": {
            "name": "Liga Pro",
            "country": "Ecuador",
            "id": 283,
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
        "concacaf_champions_league": {
            "name": "CONCACAF Champions League",
            "country": "North America",
            "id": 17,
        },
        # Asia
        "j_league": {
            "name": "J1 League",
            "country": "Japan",
            "id": 98,
        },
        "k_league": {
            "name": "K League 1",
            "country": "South Korea",
            "id": 292,
        },
        "chinese_super_league": {
            "name": "Chinese Super League",
            "country": "China",
            "id": 169,
        },
        "saudi_pro": {
            "name": "Saudi Pro League",
            "country": "Saudi Arabia",
            "id": 307,
        },
        "qatar_stars_league": {
            "name": "Qatar Stars League",
            "country": "Qatar",
            "id": 310,
        },
        "australian_a_league": {
            "name": "A-League",
            "country": "Australia",
            "id": 106,
        },
        "indian_super_league": {
            "name": "Indian Super League",
            "country": "India",
            "id": 323,
        },
        # Africa
        "caf_champions_league": {
            "name": "CAF Champions League",
            "country": "Africa",
            "id": 2001,
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
        "south_african_psl": {
            "name": "Premier Soccer League",
            "country": "South Africa",
            "id": 288,
        },
        "algerian_liga": {
            "name": "Ligue 1",
            "country": "Algeria",
            "id": 201,
        },
        "tunisian_liga": {
            "name": "Ligue 1",
            "country": "Tunisia",
            "id": 202,
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
        "french_pro_a": {
            "name": "LNB Pro A",
            "country": "France",
            "id": 299,
        },
        "german_bbl": {
            "name": "Basketball Bundesliga",
            "country": "Germany",
            "id": 300,
        },
        "eurocup": {
            "name": "EuroCup Basketball",
            "country": "Europe",
            "id": 286,
        },
        "champions_league": {
            "name": "Basketball Champions League",
            "country": "Europe",
            "id": 287,
        },
        "fibas_americas": {
            "name": "FIBA Americas League",
            "country": "Americas",
            "id": 301,
        },
        "cba": {
            "name": "Chinese Basketball Association",
            "country": "China",
            "id": 302,
        },
        "nbl": {
            "name": "National Basketball League",
            "country": "Australia",
            "id": 303,
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
        "del": {
            "name": "DEL",
            "country": "Germany",
            "id": 56,
        },
        "nla": {
            "name": "National League",
            "country": "Switzerland",
            "id": 57,
        },
        "extraliga": {
            "name": "Tipsport Extraliga",
            "country": "Czech Republic",
            "id": 58,
        },
        "ahl": {
            "name": "AHL",
            "country": "USA/Canada",
            "id": 59,
        },
        "iihf_world_championship": {
            "name": "IIHF World Championship",
            "country": "International",
            "id": 60,
        },
        "champions_hockey_league": {
            "name": "Champions Hockey League",
            "country": "Europe",
            "id": 61,
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
        "xfl": {
            "name": "XFL",
            "country": "USA",
            "id": 4,
        },
        "european_league": {
            "name": "European League of Football",
            "country": "Europe",
            "id": 5,
        },
        "arena_football": {
            "name": "Arena Football League",
            "country": "USA",
            "id": 6,
        },
    },
}

BRANDS = {
    "888starz": {
        "display_name": "888STARZ",
        "logo_prompt": "Bold and modern '888STARZ' logo with card suits ♠️♥️♦️♣️ in '888'.",
        "brand_colors": ["#b70022", "#000000", "#ffffff"],
        "slogan": "iGaming Mining Platform",
        "description": "Modern iGaming style: red/black/white, logo, and slogan.",
    },
    "melbet": {
        "display_name": "MELBET",
        "logo_prompt": "Dynamic 'MELBET' logo with yellow/black palette.",
        "brand_colors": ["#ffbe1a", "#231f20", "#ffffff"],
        "slogan": "Your Betting Partner",
        "description": "Energetic betting brand: yellow/black, fast vibe, and slogan.",
    },
    # أضف المزيد هنا...
}
