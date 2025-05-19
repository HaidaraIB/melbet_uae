from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from telegram.constants import ParseMode
from common.keyboards import (
    build_back_button,
    build_back_to_home_page_button,
    build_user_keyboard,
)
from common.common import get_lang
from common.lang_dicts import *
from start import start_command
from common.back_to_home_page import back_to_user_home_page_handler
from datetime import datetime, timedelta
from user.buy_voucher.common import (
    extract_ids,
    get_fixture_odds,
    build_gpt_prompt,
    get_fixtures,
    summarize_fixtures_with_odds_stats,
    gpt_analyze_bet_slips,
)

AMOUNT, DURATION_TYPE, DURATION_VALUE, ODDS, PREFERENCES, CONFIRM = range(6)


async def buy_voucher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["send_voucher_odd_number"],
            reply_markup=InlineKeyboardMarkup(
                build_back_to_home_page_button(lang=lang, is_admin=False)
            ),
        )
        return AMOUNT


async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        keyboard = [
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["duration_days"], callback_data="duration_days"
                ),
                InlineKeyboardButton(
                    text=BUTTONS[lang]["duration_hours"], callback_data="duration_hours"
                ),
            ],
            build_back_button(data="back_to_get_amount", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        if update.message:
            context.user_data["amount"] = update.message.text.strip()
            await update.message.reply_text(
                text=TEXTS[lang]["choose_duration_type"],
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["choose_duration_type"],
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return DURATION_TYPE


back_to_get_amount = buy_voucher


async def get_duration_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button(data="back_to_get_duration_type", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        if not update.callback_query.data.startswith("back"):
            duration_type = update.callback_query.data.replace("duration_", "")
            context.user_data["duration_type"] = duration_type
            if duration_type == "hours":
                msg = TEXTS[lang]["send_duration_hours"]
            else:
                msg = TEXTS[lang]["send_duration_days"]

            await update.callback_query.edit_message_text(
                text=msg,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return DURATION_VALUE


back_to_get_duration_type = get_amount


async def get_duration_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button(data="back_to_get_duration_value", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        value = int(update.message.text.strip())
        if update.message:
            if context.user_data["duration_type"] == "hours" and not (1 <= value <= 72):
                back_buttons = [
                    build_back_button(data="back_to_get_duration_type", lang=lang),
                    build_back_to_home_page_button(lang=lang, is_admin=False)[0],
                ]
                await update.message.reply_text(
                    text=TEXTS[lang]["send_duration_hours"],
                    reply_markup=InlineKeyboardMarkup(back_buttons),
                )
                return DURATION_VALUE

            context.user_data["duration_value"] = value
            await update.message.reply_text(
                text=TEXTS[lang]["send_odds"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["send_odds"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return ODDS


back_to_get_duration_value = get_duration_type


async def get_odds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button(data="back_to_get_odds", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        if update.message:
            odds = float(update.message.text.strip())
            context.user_data["odds"] = odds

            await update.message.reply_text(
                text=TEXTS[lang]["send_preferences"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["send_preferences"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return PREFERENCES


back_to_get_odds = get_duration_value


async def get_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        context.user_data["preferences"] = update.message.text.strip()
        price = round(float(context.user_data["odds"]) * 5, 2)
        keyboard = [
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["confirm_payment"],
                    callback_data="confirm_payment",
                ),
                InlineKeyboardButton(
                    text=BUTTONS[lang]["cancel_voucher"],
                    callback_data="cancel_voucher",
                ),
            ],
            build_back_button(data="back_to_get_preferences", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        await update.message.reply_text(
            text=TEXTS[lang]["voucher_summary"].format(
                context.user_data["amount"],
                f"{context.user_data['duration_value']} {context.user_data['duration_type']}",
                context.user_data["odds"],
                context.user_data["preferences"],
                price,
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CONFIRM


back_to_get_preferences = get_odds


async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        if update.callback_query.data == "confirm_payment":
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["payment_confirmed"],
            )

            now = datetime.now()
            duration_value = int(context.user_data["duration_value"])
            duration_type = context.user_data["duration_type"]

            from_date = now
            to_date = now + (
                timedelta(hours=duration_value)
                if duration_type == "hours"
                else timedelta(days=duration_value)
            )
            
            league_id, team_id = extract_ids(context.user_data["preferences"])

            fixtures = get_fixtures(league_id, team_id, from_date, to_date)
            fixtures_summary = summarize_fixtures_with_odds_stats(fixtures, max_count=8)

            prompt = build_gpt_prompt(context.user_data, fixtures_summary)
            reply = await gpt_analyze_bet_slips(prompt)
            await update.callback_query.edit_message_text(
                text=reply,
                disable_web_page_preview=True,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["voucher_canceled"],
                reply_markup=build_user_keyboard(lang=lang),
            )


buy_voucher_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            buy_voucher,
            "^buy_voucher$",
        )
    ],
    states={
        AMOUNT: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_amount,
            )
        ],
        DURATION_TYPE: [
            CallbackQueryHandler(
                get_duration_type,
                "^duration_",
            )
        ],
        DURATION_VALUE: [
            MessageHandler(
                filters=filters.Regex("^[0-9]+$"),
                callback=get_duration_value,
            )
        ],
        ODDS: [
            MessageHandler(
                filters=filters.Regex("^[0-9]+\.?[0-9]*$"),
                callback=get_odds,
            )
        ],
        PREFERENCES: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_preferences,
            )
        ],
        CONFIRM: [
            CallbackQueryHandler(
                handle_payment,
                "^(confirm_payment|cancel_voucher)$",
            )
        ],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(back_to_get_amount, "^back_to_get_amount$"),
        CallbackQueryHandler(back_to_get_duration_type, "^back_to_get_duration_type$"),
        CallbackQueryHandler(back_to_get_preferences, "^back_to_get_preferences$"),
        CallbackQueryHandler(
            back_to_get_duration_value, "^back_to_get_duration_value$"
        ),
    ],
    name="buy_voucher_conv",
    persistent=True,
)
