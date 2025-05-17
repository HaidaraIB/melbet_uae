from telegram import Update, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)
import json
from client.client_calls.common import openai
from Config import Config
from utils.api_calls import search_team_id_by_name, get_h2h, BASE_URL
from common.lang_dicts import *
from common.common import get_lang, format_datetime
from common.keyboards import build_back_to_home_page_button, build_back_button
from common.back_to_home_page import back_to_user_home_page_handler
from start import start_command
from datetime import datetime

GAME_INFO, PAY = range(2)


async def analyze_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)

        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["request_game_info"],
            reply_markup=InlineKeyboardMarkup(
                build_back_to_home_page_button(lang=lang, is_admin=False)
            ),
        )
        return GAME_INFO


async def handle_match_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        wait_msg = await update.message.reply_text(
            text=TEXTS[lang]["plz_wait"],
        )
        parsed = await ask_gpt_about_match(update.message.text)
        parsed_json = json.loads(parsed)

        teams1 = search_team_id_by_name(name=parsed_json["team1"].replace("-", " "))
        teams2 = search_team_id_by_name(name=parsed_json["team2"].replace("-", " "))

        if not teams1 or not teams2:
            await update.message.reply_text(text=TEXTS[lang]["either_teams_wrong"])
            return

        for team1 in teams1:
            for team2 in teams2:
                match = get_h2h(h2h=f"{team1['team']['id']}-{team2['team']['id']}")
                if match:
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                text=BUTTONS[lang]["pay"],
                                callback_data="pay",
                            )
                        ],
                        build_back_button(data="back_to_handle_match_input", lang=lang),
                        build_back_to_home_page_button(lang=lang, is_admin=False)[0],
                    ]
                    await wait_msg.edit_text(
                        text=TEXTS[lang]["analyze_game_ai_result"].format(
                            team1["team"]["name"],
                            team2["team"]["name"],
                            format_datetime(datetime.fromisoformat(match["date"])),
                            match["league"],
                            match["venue"],
                            match["teams"],
                        ),
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                    return PAY
        await wait_msg.edit_text(
            text=TEXTS[lang]["no_upcoming_games"],
            reply_markup=InlineKeyboardMarkup(
                build_back_to_home_page_button(lang=lang, is_admin=False)
            ),
        )


async def ask_gpt_about_match(user_question):
    prompt = f" User asked: {user_question} Extract clearly the two team names in lower case English letters to search for them in {BASE_URL} api. the priority is for the most famous teams. Return as JSON with: team1, team2 "
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


back_to_handle_match_input = analyze_game


async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        await update.callback_query.answer(
            text=TEXTS[lang]["soon"],
            show_alert=True,
        )


analyze_game_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            analyze_game,
            "^analyze_game$",
        )
    ],
    states={
        GAME_INFO: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=handle_match_input,
            )
        ],
        PAY: [
            CallbackQueryHandler(
                pay,
                "^pay$",
            )
        ],
    },
    fallbacks=[
        back_to_user_home_page_handler,
        start_command,
        CallbackQueryHandler(
            back_to_handle_match_input,
            "^back_to_handle_match_input$",
        ),
    ],
)
