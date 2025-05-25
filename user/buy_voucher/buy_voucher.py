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
    summarize_fixtures_with_odds_stats,
    generate_multimatch_coupon,
    build_preferences_keyboard,
    parse_user_request,
)
import models

(
    DURATION_TYPE,
    DURATION_VALUE,
    ODDS,
    PREFERENCES,
    PREF,
    CONFIRM,
) = range(6)


async def buy_voucher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["send_voucher_odd_number"],
            reply_markup=InlineKeyboardMarkup(
                build_back_to_home_page_button(lang=lang, is_admin=False)
            ),
        )
        return ODDS


async def get_odds(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            build_back_button(data="back_to_get_odds", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        if update.message:
            context.user_data["odds"] = update.message.text.strip()
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


back_to_get_odds = buy_voucher


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


back_to_get_duration_type = get_odds


async def get_duration_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        keyboard = [
            *build_preferences_keyboard(lang=lang),
            build_back_button(data="back_to_get_duration_value", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        value = int(update.message.text.strip())
        duration_type = context.user_data["duration_type"]
        if update.message:
            if duration_type == "hours" and not (1 <= value <= 72):
                back_buttons = [
                    build_back_button(data="back_to_get_duration_type", lang=lang),
                    build_back_to_home_page_button(lang=lang, is_admin=False)[0],
                ]
                await update.message.reply_text(
                    text=TEXTS[lang]["send_duration_hours"],
                    reply_markup=InlineKeyboardMarkup(back_buttons),
                )
                return
            elif duration_type == "days" and not (1 <= value <= 10):
                back_buttons = [
                    build_back_button(data="back_to_get_duration_type", lang=lang),
                    build_back_to_home_page_button(lang=lang, is_admin=False)[0],
                ]
                await update.message.reply_text(
                    text=TEXTS[lang]["send_duration_days"],
                    reply_markup=InlineKeyboardMarkup(back_buttons),
                )
                return

            context.user_data["duration_value"] = value
            await update.message.reply_text(
                text=TEXTS[lang]["choose_preferences"],
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["choose_preferences"],
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return PREFERENCES

back_to_get_duration_value = get_duration_type


async def choose_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button(data="back_to_get_preferences", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        if not update.callback_query.data.startswith("back"):
            pref = update.callback_query.data.replace("choose_pref_", "")
            context.user_data["preferences"] = pref
        else:
            pref = context.user_data["preferences"]

        if pref in ["league", "matches"]:
            await update.callback_query.edit_message_text(
                text=(
                    TEXTS[lang]["send_league_pref"]
                    if pref == "league"
                    else TEXTS[lang]["send_matches_pref"]
                ),
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return PREF

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
            *back_buttons,
        ]
        price = round(float(context.user_data["odds"]) * 5, 2)
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["voucher_summary"].format(
                context.user_data["odds"],
                f"{context.user_data['duration_value']} {context.user_data['duration_type']}",
                "Choose for me",
                price,
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CONFIRM


back_to_get_preferences = get_duration_value


async def get_pref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        pref = context.user_data["preferences"]
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
            build_back_button(data="back_to_get_league_pref", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        price = round(float(context.user_data["odds"]) * 5, 2)
        if update.message:
            if pref == "league":
                league_pref = update.message.text
                context.user_data["league_pref"] = league_pref
            elif pref == "matches":
                matches_text = update.message.text.strip()
                gpt_response = await parse_user_request(
                    matches_text=matches_text, desired_odds=context.user_data["odds"]
                )
                matches_list = gpt_response["structured_matches"]
                if not matches_list:
                    await update.message.reply_text(
                        text=TEXTS[lang]["gpt_buy_voucher_reply_empty"]
                    )
                    return
                context.user_data["matches_pref"] = matches_list
            await update.message.reply_text(
                text=TEXTS[lang]["voucher_summary"].format(
                    context.user_data["odds"],
                    f"{context.user_data['duration_value']} {context.user_data['duration_type']}",
                    (
                        f"League({league_pref})"
                        if pref == "league"
                        else "\n".join(matches_list)
                    ),
                    price,
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            league_pref = context.user_data["league_pref"]
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["voucher_summary"].format(
                    context.user_data["odds"],
                    f"{context.user_data['duration_value']} {context.user_data['duration_type']}",
                    league_pref,
                    price,
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return CONFIRM


back_to_get_league_pref = choose_preferences


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

        now = datetime.now()
        if context.user_data["duration_type"] == "hours":
            to = now + timedelta(hours=context.user_data["duration_value"])
        else:
            to = now + timedelta(days=context.user_data["duration_value"])

        pref = context.user_data["preferences"]
        with models.session_scope() as session:
            if pref == "league":
                league_id, _ = extract_ids(context.user_data["league_pref"])
                cached_fixtures = session.query(models.CachedFixture).filter(
                    models.CachedFixture.league_id == league_id,
                    models.CachedFixture.fixture_date >= now,
                    models.CachedFixture.fixture_date <= to,
                ).all()
                fixtures = [f.data for f in cached_fixtures]  # Extract the JSON data
            elif pref == "matches":
                cached_fixtures = session.query(models.CachedFixture).filter(
                    models.CachedFixture.fixture_date >= now,
                    models.CachedFixture.fixture_date <= to,
                ).all()
                all_fixtures = [f.data for f in cached_fixtures]  # Extract the JSON data
                fixtures = []
                for user_match in context.user_data["matches_pref"]:
                    for fixture in all_fixtures:
                        fixture_strs = [
                            f"{fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}".lower(),
                            f"{fixture['teams']['away']['name']} vs {fixture['teams']['home']['name']}".lower(),
                        ]
                        if user_match.lower() in fixture_strs:
                            fixtures.append(fixture)
                            break
                if not fixtures:
                    await q.edit_message_text(
                        text=TEXTS[lang]["gpt_buy_voucher_reply_empty"],
                        reply_markup=build_user_keyboard(lang=lang),
                    )
                    return ConversationHandler.END
            else:
                cached_fixtures = session.query(models.CachedFixture).filter(
                    models.CachedFixture.fixture_date >= now,
                    models.CachedFixture.fixture_date <= to,
                ).all()
                fixtures = [f.data for f in cached_fixtures]  # Extract the JSON data

            fixtures_summary = summarize_fixtures_with_odds_stats(fixtures=fixtures, session=session)

            # Call GPT
            coupon_json, message_md = await generate_multimatch_coupon(
                fixtures_summary=fixtures_summary, odds=context.user_data["odds"]
            )

            if not message_md:
                await q.edit_message_text(
                    text=TEXTS[lang]["gpt_buy_voucher_reply_empty"],
                    reply_markup=build_user_keyboard(lang=lang),
                )
                return ConversationHandler.END

            # Store each tip in DB
            for match_block in coupon_json["matches"]:
                label = match_block["teams"]  # e.g. "Team A vs Team B"
                fx = next(
                    f
                    for f in fixtures
                    if f["teams"]["home"]["name"] + " vs " + f["teams"]["away"]["name"]
                    == label
                )
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
                    session.add(recommendation)
                session.commit()

        # Split and send final Markdown message if it's too long
        max_length = 4096  # Telegram's message length limit
        if len(message_md) <= max_length:
            try:
                await q.edit_message_text(
                    text=message_md, parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                await q.edit_message_text(
                    text=f"Error: {e}", parse_mode=ParseMode.MARKDOWN
                )
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
        ODDS: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_odds,
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
        PREFERENCES: [
            CallbackQueryHandler(
                choose_preferences,
                "^choose_pref",
            )
        ],
        PREF: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_pref,
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
        CallbackQueryHandler(back_to_get_odds, "^back_to_get_odds$"),
        CallbackQueryHandler(back_to_get_duration_type, "^back_to_get_duration_type$"),
        CallbackQueryHandler(back_to_get_preferences, "^back_to_get_preferences$"),
        CallbackQueryHandler(
            back_to_get_duration_value, "^back_to_get_duration_value$"
        ),
        CallbackQueryHandler(back_to_get_league_pref, "^back_to_get_league_pref$"),
    ],
    name="buy_voucher_conv",
    persistent=True,
)
