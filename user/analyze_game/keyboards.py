from telegram import InlineKeyboardButton
from common.lang_dicts import *
import models


def build_sports_keyboard(lang: models.Language, prefix: str):
    return [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["football"],
                callback_data=f"{prefix}_football",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["basketball"],
                callback_data=f"{prefix}_basketball",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["american_football"],
                callback_data=f"{prefix}_american_football",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["hockey"],
                callback_data=f"{prefix}_hockey",
            )
        ],
    ]


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
