from telegram import Update, Chat, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from common.lang_dicts import *
from common.common import get_lang
from common.keyboards import build_back_to_home_page_button, build_back_button
from common.back_to_home_page import back_to_user_home_page_handler
from start import start_command
from utils.api_calls import get_team, get_h2h, _send_post_match_stats


HOME_TEAM, AWAY_TEAM, DATE = range(3)


async def analyze_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)

        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["request_home_team"],
            reply_markup=InlineKeyboardMarkup(
                build_back_to_home_page_button(lang=lang, is_admin=False)
            ),
        )
        return HOME_TEAM


async def get_home_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button(data="back_to_get_home_team", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        if update.message:
            home_team = update.message.text
            context.user_data["home_team"] = home_team.lower()
            await update.message.reply_text(
                text=TEXTS[lang]["request_away_team"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["request_away_team"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return AWAY_TEAM


back_to_get_home_team = analyze_game


async def get_away_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button(data="back_to_get_away_team", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        if update.message:
            away_team = update.message.text
            context.user_data["away_team"] = away_team.lower()
            await update.message.reply_text(
                text=TEXTS[lang]["request_date"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["request_date"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return DATE


back_to_get_away_team = get_home_team


async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        home_team = get_team(name=context.user_data["home_team"])
        if not home_team:
            await update.message.reply_text(text=TEXTS[lang]["wrong_home_team"])
            return
        away_team = get_team(name=context.user_data["away_team"])
        if not away_team:
            await update.message.reply_text(text=TEXTS[lang]["wrong_away_team"])
            return
        h2h = get_h2h(
            h2h=f"{home_team[0]['team']['id']}-{away_team[0]['team']['id']}",
            d=update.message.text,
        )
        if not h2h:
            await update.message.reply_text(
                text=TEXTS[lang]["no_h2h"].format(
                    home_team[0]["team"]["name"],
                    away_team[0]["team"]["name"],
                    update.message.text,
                )
            )
            return
        await _send_post_match_stats(
            chat_id=update.effective_chat.id,
            fixture_id=h2h[0]["fixture"]["id"],
            context=context,
        )
        return ConversationHandler.END


analyze_game_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            analyze_game,
            "^analyze_game$",
        ),
    ],
    states={
        HOME_TEAM: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_home_team,
            ),
        ],
        AWAY_TEAM: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_away_team,
            ),
        ],
        DATE: [
            MessageHandler(
                filters=filters.Regex("^[0-9]{4}-[0-9]{2}-[0-9]{2}$"),
                callback=get_date,
            ),
        ],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(back_to_get_home_team, "^back_to_get_home_team$"),
        CallbackQueryHandler(back_to_get_away_team, "^back_to_get_away_team$"),
    ],
    name="analyze_game_conv",
    persistent=True,
)
