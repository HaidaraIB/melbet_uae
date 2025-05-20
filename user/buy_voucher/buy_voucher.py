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
    get_fixtures,
    summarize_fixtures_with_odds_stats,
    generate_multimatch_coupon,
)
import models

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
        q = update.callback_query
        await q.answer()
        # Cancel if not confirmed
        if q.data != "confirm_payment":
            await q.edit_message_text(
                text=TEXTS[lang]["voucher_canceled"],
                reply_markup=build_user_keyboard(lang=lang),
            )
            return ConversationHandler.END

        # Show waiting message
        await q.edit_message_text(text=TEXTS[lang]["payment_confirmed"])

        # Prepare fixtures list & summary
        league_id, team_id = extract_ids(context.user_data["preferences"])
        now = datetime.now()
        if context.user_data["duration_type"] == "hours":
            to = now + timedelta(hours=context.user_data["duration_value"])
        else:
            to = now + timedelta(days=context.user_data["duration_value"])

        fixtures = await get_fixtures(league_id, team_id, now, to)
        fixtures_summary = summarize_fixtures_with_odds_stats(fixtures)

        # Call GPT
        coupon_json, message_md = await generate_multimatch_coupon(fixtures_summary)

        # Store each tip in DB
        for match_block in coupon_json["matches"]:
            label = match_block["teams"]  # e.g. "Team A vs Team B"
            fx = next(
                f
                for f in fixtures
                if f["teams"]["home"]["name"] + " vs " + f["teams"]["away"]["name"]
                == label
            )
            with models.session_scope() as s:
                for tip in match_block["tips"]:
                    # إضافة التوصيات الجديدة
                    recommendation = models.FixtureRecommendation(
                        user_id=update.effective_user.id,
                        fixture_id=fx["fixture"]["id"],
                        match_date=fx["fixture"]["date"],
                        league_id=fx["league"]["id"],
                        title=f"{label} → {tip['selection']}",
                        market=tip["market"],
                        selection=tip["selection"],
                        threshold=tip.get("threshold"),
                    )
                    s.add(recommendation)
                s.commit()

        # Split and send final Markdown message if it's too long
        max_length = 4096  # Telegram's message length limit
        if len(message_md) <= max_length:
            await q.edit_message_text(text=message_md, parse_mode=ParseMode.MARKDOWN)
        else:
            # Split the message into parts
            parts = []
            while message_md:
                if len(message_md) > max_length:
                    # Find the last newline before the limit to avoid breaking mid-line
                    split_at = message_md.rfind("\n", 0, max_length)
                    if split_at == -1:  # No newline found, split at max_length
                        split_at = max_length
                    parts.append(message_md[:split_at])
                    message_md = message_md[split_at:].lstrip()
                else:
                    parts.append(message_md)
                    message_md = ""

            # Send the first part by editing the original message
            await q.edit_message_text(text=parts[0], parse_mode=ParseMode.MARKDOWN)

            # Send remaining parts as new messages
            for part in parts[1:]:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=part,
                    parse_mode=ParseMode.MARKDOWN,
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
