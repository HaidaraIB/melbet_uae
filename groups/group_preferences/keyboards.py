from telegram import InlineKeyboardButton
from groups.group_preferences.constants import *
from groups.group_preferences.lang_dicts import *


def build_lang_kb():
    return [
        [
            InlineKeyboardButton(
                text=LANGUAGES[k],
                callback_data=f"set_lang_{k}",
            )
        ]
        for k in LANGUAGES
    ]


def build_dialect_kb(lang: str):
    return [
        [
            InlineKeyboardButton(
                text=DIALECTS[lang][k],
                callback_data=f"set_dialect_{k}",
            )
        ]
        for k in DIALECTS[lang]
    ]


def build_sports_kb(lang: Language, selected=None):
    kb = []
    for code, name in SPORTS.items():
        check = "✅" if selected and code in selected else "⬜️"
        kb.append(
            [
                InlineKeyboardButton(
                    text=f"{check} {name[lang]}",
                    callback_data=f"toggle_sport_{code}",
                )
            ]
        )
    kb.append(
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["continue"],
                callback_data="sports_done",
            )
        ]
    )
    return kb


def build_leagues_kb(sport: str, lang: Language, selected_ids=None):
    kb = []
    for league in LEAGUES[sport].values():
        check = "✅" if selected_ids and league["id"] in selected_ids else "⬜️"
        kb.append(
            [
                InlineKeyboardButton(
                    text=f"{check} {league['name']}",
                    callback_data=f"toggle_league_{sport}_{league['id']}",
                )
            ]
        )
    kb.append(
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["continue"],
                callback_data=f"leagues_done_{sport}",
            )
        ]
    )
    return kb
