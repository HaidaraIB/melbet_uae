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
from user.buy_voucher.common import (
    summarize_fixtures_with_odds_stats,
    generate_multimatch_coupon,
    parse_user_request,
)
from user.buy_voucher.keyboards import (
    build_get_voucher_confirmation_keyboard,
    build_preferences_keyboard,
)
from user.buy_voucher.functions import calc_from_to_dates_and_duration_in_days
from user.analyze_game.keyboards import build_sports_keyboard
from utils.api_calls_by_sport import get_fixtures_by_sport
from utils.functions import filter_fixtures
import models

(
    DURATION_TYPE,
    DURATION_VALUE,
    ODDS,
    PREFERENCES,
    MATCHES,
    SPORT,
    LEAGUE,
    CONFIRM,
) = range(8)


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
            odds = float(update.message.text.strip())
            if odds <= 0:
                await update.message.reply_text(
                    text=TEXTS[lang]["send_voucher_odd_number"],
                    reply_markup=InlineKeyboardMarkup(
                        build_back_to_home_page_button(lang=lang, is_admin=False)
                    ),
                )
                return
            context.user_data["odds"] = odds
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
        duration_type = context.user_data["duration_type"]
        if update.message:
            value = int(update.message.text.strip())
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
        odds = context.user_data["odds"]
        back_buttons = [
            build_back_button(data="back_to_get_preferences", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        if not update.callback_query.data.startswith("back"):
            pref = update.callback_query.data.replace("choose_pref_", "")
            context.user_data["preferences"] = pref
        else:
            pref = context.user_data["preferences"]

        if pref == "sport":
            keyboard = [
                *build_sports_keyboard(lang=lang, prefix="pref"),
                *back_buttons,
            ]
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["choose_sport"],
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return SPORT

        elif pref == "matches":
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["send_matches_pref"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return MATCHES
        context.user_data["current_sub_id"] = None
        keyboard = build_get_voucher_confirmation_keyboard(
            user_id=update.effective_user.id, lang=lang, odds=odds
        )
        keyboard.append(back_buttons[0])
        keyboard.append(back_buttons[1])
        price = round(odds * 5, 2)
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["voucher_summary"].format(
                f"{context.user_data['duration_value']} {context.user_data['duration_type']}",
                odds,
                price,
                "Choose for me",
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CONFIRM


back_to_get_preferences = get_duration_value


async def choose_sport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button(data="back_to_choose_sport", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        if not update.callback_query.data.startswith("back"):
            sport = update.callback_query.data.replace("pref_", "")
            context.user_data["sport_pref"] = sport
        else:
            sport = context.user_data["sport_pref"]
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["send_league_pref"],
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return LEAGUE


back_to_choose_sport = choose_preferences


async def get_league(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        odds = context.user_data["odds"]
        sport_pref = context.user_data["sport_pref"]
        back_buttons = [
            build_back_button(data="back_to_get_league", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        context.user_data["current_sub_id"] = None
        keyboard = build_get_voucher_confirmation_keyboard(
            user_id=update.effective_user.id, lang=lang, odds=odds
        )
        keyboard.append(back_buttons[0])
        keyboard.append(back_buttons[1])
        price = round(float(odds) * 5, 2)
        if update.message:
            wait_msg = await update.message.reply_text(text=TEXTS[lang]["plz_wait"])
            league = await parse_user_request(league=update.message.text)
            if not league:
                await wait_msg.edit_text(
                    text=TEXTS[lang]["gpt_buy_voucher_reply_empty"]
                )
                return
            fixtures = []
            now, duration_in_days = calc_from_to_dates_and_duration_in_days(
                duration_type=context.user_data["duration_type"],
                duration_value=context.user_data["duration_value"],
            )
            all_fixtures = await get_fixtures_by_sport(
                from_date=now,
                duration_in_days=duration_in_days,
                sport=sport_pref,
            )
            for fix in all_fixtures:
                if fix["league_name"] == league["league_name"]:
                    fixtures.append(fix)
            if not fixtures:
                await wait_msg.edit_text(
                    text=TEXTS[lang]["gpt_buy_voucher_reply_empty"]
                )
                return
            context.user_data["buy_voucher_sport_pref_fixtures"] = fixtures
            context.user_data["league_pref"] = league["league_name"]
            await wait_msg.edit_text(
                text=TEXTS[lang]["voucher_summary"].format(
                    f"{context.user_data['duration_value']} {context.user_data['duration_type']}",
                    odds,
                    price,
                    (f"Sport({sport_pref})\n" f"League({league['league_name']})"),
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            league_pref = context.user_data["league_pref"]
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["voucher_summary"].format(
                    f"{context.user_data['duration_value']} {context.user_data['duration_type']}",
                    odds,
                    price,
                    (f"Sport({sport_pref})\n" f"League({league_pref})"),
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return CONFIRM


back_to_get_league = choose_sport


async def get_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        odds = context.user_data["odds"]
        back_buttons = [
            build_back_button(data="back_to_get_matches", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        context.user_data["current_sub_id"] = None
        keyboard = build_get_voucher_confirmation_keyboard(
            user_id=update.effective_user.id, lang=lang, odds=odds
        )
        keyboard.append(back_buttons[0])
        keyboard.append(back_buttons[1])
        price = round(float(odds) * 5, 2)
        if update.message:
            wait_msg = await update.message.reply_text(text=TEXTS[lang]["plz_wait"])
            matches_text = update.message.text.strip()
            matches_list = await parse_user_request(matches_text=matches_text)
            if not matches_list:
                await wait_msg.edit_text(
                    text=TEXTS[lang]["gpt_buy_voucher_reply_empty"]
                )
                return
            now, duration_in_days = calc_from_to_dates_and_duration_in_days(
                duration_type=context.user_data["duration_type"],
                duration_value=context.user_data["duration_value"],
            )
            fixtures = []
            sports = set([match["sport"].lower() for match in matches_list])
            all_fixtures = []
            for s in sports:
                all_fixtures += await get_fixtures_by_sport(
                    from_date=now,
                    duration_in_days=duration_in_days,
                    sport=s,
                )
            for match in matches_list:
                for fix in all_fixtures:
                    if match["title"] in [
                        f"{fix['home_name']} vs {fix['away_name']}",
                        f"{fix['away_name']} vs {fix['home_name']}",
                    ]:
                        fixtures.append(fix)
            if not fixtures:
                await wait_msg.edit_text(
                    text=TEXTS[lang]["gpt_buy_voucher_reply_empty"]
                )
                return
            context.user_data["buy_voucher_matches_pref_fixtures"] = fixtures
            context.user_data["matches_pref"] = matches_list
            await wait_msg.edit_text(
                text=TEXTS[lang]["voucher_summary"].format(
                    f"{context.user_data['duration_value']} {context.user_data['duration_type']}",
                    odds,
                    price,
                    "\n".join([match["title"] for match in matches_list]),
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            matches_list = context.user_data["matches_pref"]
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["voucher_summary"].format(
                    f"{context.user_data['duration_value']} {context.user_data['duration_type']}",
                    odds,
                    price,
                    "\n".join([match["title"] for match in matches_list]),
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return CONFIRM


back_to_get_matches = choose_preferences


async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        q = update.callback_query
        await q.answer()
        if q.data == "cancel_voucher":
            await q.edit_message_text(
                text=TEXTS[lang]["voucher_canceled"],
                reply_markup=build_user_keyboard(lang=lang),
            )
            return ConversationHandler.END

        elif q.data.startswith("use_sub"):
            with models.session_scope() as s:
                sub_id = int(q.data.replace("use_sub_", ""))
                sub = s.get(models.Subscription, sub_id)
                sub.remaining_vouchers -= 1
                s.commit()

        await q.edit_message_text(text=TEXTS[lang]["payment_confirmed"])

        now, duration_in_days = calc_from_to_dates_and_duration_in_days(
            duration_type=context.user_data["duration_type"],
            duration_value=context.user_data["duration_value"],
        )

        pref = context.user_data["preferences"]
        odds = context.user_data["odds"]
        fixtures = []
        if pref == "sport":
            fixtures = context.user_data["buy_voucher_sport_pref_fixtures"]
        elif pref == "matches":
            fixtures = context.user_data["buy_voucher_matches_pref_fixtures"]
        else:
            odds = [odds * 0.5, odds * 0.3, odds * 0.1, odds * 0.1]
            football_fixtures = await get_fixtures_by_sport(
                from_date=now,
                duration_in_days=duration_in_days,
                sport="football",
            )
            basketball_fixtures = await get_fixtures_by_sport(
                from_date=now,
                duration_in_days=duration_in_days,
                sport="basketball",
            )
            american_football_fixtures = await get_fixtures_by_sport(
                from_date=now,
                duration_in_days=duration_in_days,
                sport="american_football",
            )
            hockey_fixtures = await get_fixtures_by_sport(
                from_date=now,
                duration_in_days=duration_in_days,
                sport="hockey",
            )
            fixtures = [
                *filter_fixtures(fixtures=football_fixtures, sport="football"),
                *filter_fixtures(fixtures=basketball_fixtures, sport="basketball"),
                *filter_fixtures(
                    fixtures=american_football_fixtures, sport="american football"
                ),
                *filter_fixtures(fixtures=hockey_fixtures, sport="hockey"),
            ]

        fixtures_summary = await summarize_fixtures_with_odds_stats(fixtures=fixtures)

        coupon_json, message_md = await generate_multimatch_coupon(
            fixtures_summary=fixtures_summary, odds=odds
        )

        if not message_md:
            await q.edit_message_text(
                text=TEXTS[lang]["gpt_buy_voucher_reply_empty"],
                reply_markup=build_user_keyboard(lang=lang),
            )
            return ConversationHandler.END
        with models.session_scope() as session:
            # Store each tip in DB
            for match_block in coupon_json["matches"]:
                label = match_block["teams"]  # e.g. "Team A vs Team B"
                fx = next(
                    f
                    for f in fixtures
                    if label
                    in [
                        f"{f['home_name']} vs {f['away_name']}",
                        f"{f['away_name']} vs {f['home_name']}",
                    ]
                )
                for tip in match_block["tips"]:
                    # إضافة التوصيات الجديدة
                    recommendation = models.FixtureRecommendation(
                        user_id=update.effective_user.id,
                        fixture_id=fx["fixture_id"],
                        match_date=fx["date"],
                        league_id=fx["league_id"],
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
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_odds,
            )
        ],
        PREFERENCES: [
            CallbackQueryHandler(
                choose_preferences,
                "^choose_pref",
            )
        ],
        MATCHES: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_matches,
            )
        ],
        SPORT: [
            CallbackQueryHandler(
                choose_sport,
                "^pref_((football)|(basketball)|(american_football)|(hockey))$",
            )
        ],
        LEAGUE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_league,
            )
        ],
        CONFIRM: [
            CallbackQueryHandler(
                handle_payment,
                "^(confirm_payment|cancel_voucher|use_sub)",
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
        CallbackQueryHandler(back_to_get_matches, "^back_to_get_matches$"),
        CallbackQueryHandler(back_to_get_league, "^back_to_get_league$"),
        CallbackQueryHandler(back_to_choose_sport, "^back_to_choose_sport$"),
    ],
    name="buy_voucher_conv",
    persistent=True,
)


# async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.effective_chat.type == Chat.PRIVATE:
#         lang = get_lang(update.effective_user.id)
#         q = update.callback_query
#         await q.answer()
#         # Cancel if not confirmed
#         if q.data == "cancel_voucher":
#             await q.edit_message_text(
#                 text=TEXTS[lang]["voucher_canceled"],
#                 reply_markup=build_user_keyboard(lang=lang),
#             )
#             return ConversationHandler.END

#         elif q.data.startswith("use_sub"):
#             with models.session_scope() as s:
#                 sub_id = int(q.data.replace("use_sub_", ""))
#                 sub = s.get(models.Subscription, sub_id)
#                 sub.remaining_vouchers -= 1
#                 s.commit()

#         # Show waiting message
#         await q.edit_message_text(text=TEXTS[lang]["payment_confirmed"])

#         now = datetime.now(TIMEZONE)
#         if context.user_data["duration_type"] == "hours":
#             to = now + timedelta(hours=context.user_data["duration_value"])
#         else:
#             to = now + timedelta(days=context.user_data["duration_value"])

#         pref = context.user_data["preferences"]
#         with models.session_scope() as session:
#             if pref == "league":
#                 league_id, _ = extract_ids(context.user_data["league_pref"])
#                 cached_fixtures = (
#                     session.query(models.CachedFixture)
#                     .filter(
#                         models.CachedFixture.league_id == league_id,
#                         models.CachedFixture.fixture_date >= now,
#                         models.CachedFixture.fixture_date <= to,
#                     )
#                     .all()
#                 )
#                 fixtures = [f.data for f in cached_fixtures]  # Extract the JSON data
#             elif pref == "matches":
#                 cached_fixtures = (
#                     session.query(models.CachedFixture)
#                     .filter(
#                         models.CachedFixture.fixture_date >= now,
#                         models.CachedFixture.fixture_date <= to,
#                     )
#                     .all()
#                 )
#                 all_fixtures = [
#                     f.data for f in cached_fixtures
#                 ]  # Extract the JSON data
#                 fixtures = []
#                 for user_match in context.user_data["matches_pref"]:
#                     for fixture in all_fixtures:
#                         fixture_strs = [
#                             f"{fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}".lower(),
#                             f"{fixture['teams']['away']['name']} vs {fixture['teams']['home']['name']}".lower(),
#                         ]
#                         if user_match.lower() in fixture_strs:
#                             fixtures.append(fixture)
#                             break
#                 if not fixtures:
#                     await q.edit_message_text(
#                         text=TEXTS[lang]["gpt_buy_voucher_reply_empty"],
#                         reply_markup=build_user_keyboard(lang=lang),
#                     )
#                     return ConversationHandler.END
#             else:
#                 cached_fixtures = (
#                     session.query(models.CachedFixture)
#                     .filter(
#                         models.CachedFixture.fixture_date >= now,
#                         models.CachedFixture.fixture_date <= to,
#                     )
#                     .all()
#                 )
#                 fixtures = [f.data for f in cached_fixtures]  # Extract the JSON data

#             fixtures_summary = summarize_fixtures_with_odds_stats(
#                 fixtures=fixtures, session=session
#             )

#             # Call GPT
#             coupon_json, message_md = await generate_multimatch_coupon(
#                 fixtures_summary=fixtures_summary, odds=context.user_data["odds"]
#             )

#             if not message_md:
#                 await q.edit_message_text(
#                     text=TEXTS[lang]["gpt_buy_voucher_reply_empty"],
#                     reply_markup=build_user_keyboard(lang=lang),
#                 )
#                 return ConversationHandler.END

#             # Store each tip in DB
#             for match_block in coupon_json["matches"]:
#                 label = match_block["teams"]  # e.g. "Team A vs Team B"
#                 fx = next(
#                     f
#                     for f in fixtures
#                     if f["teams"]["home"]["name"] + " vs " + f["teams"]["away"]["name"]
#                     == label
#                 )
#                 for tip in match_block["tips"]:
#                     # إضافة التوصيات الجديدة
#                     recommendation = models.FixtureRecommendation(
#                         user_id=update.effective_user.id,
#                         fixture_id=fx["fixture"]["id"],
#                         match_date=fx["fixture"]["date"],
#                         league_id=fx["league"]["id"],
#                         title=f"{label} → {tip['selection']}",
#                         market=tip["market"],
#                         selection=tip["selection"],
#                         threshold=tip.get("threshold"),
#                     )
#                     session.add(recommendation)
#                 session.commit()

#         # Split and send final Markdown message if it's too long
#         max_length = 4096  # Telegram's message length limit
#         if len(message_md) <= max_length:
#             try:
#                 await q.edit_message_text(
#                     text=message_md, parse_mode=ParseMode.MARKDOWN
#                 )
#             except Exception as e:
#                 await q.edit_message_text(
#                     text=f"Error: {e}", parse_mode=ParseMode.MARKDOWN
#                 )
#         else:
#             # Split the message into parts
#             parts = []
#             while message_md:
#                 if len(message_md) > max_length:
#                     # Find the last newline before the limit to avoid breaking mid-line
#                     split_at = message_md.rfind("\n", 0, max_length)
#                     if split_at == -1:  # No newline found, split at max_length
#                         split_at = max_length
#                     parts.append(message_md[:split_at])
#                     message_md = message_md[split_at:].lstrip()
#                 else:
#                     parts.append(message_md)
#                     message_md = ""

#             # Send the first part by editing the original message
#             await q.edit_message_text(text=parts[0], parse_mode=ParseMode.MARKDOWN)

#             # Send remaining parts as new messages
#             for part in parts[1:]:
#                 await context.bot.send_message(
#                     chat_id=update.effective_chat.id,
#                     text=part,
#                     parse_mode=ParseMode.MARKDOWN,
#                 )
