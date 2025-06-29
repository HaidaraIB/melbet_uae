from telegram import Update, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)
from telegram.constants import ParseMode
from utils.api_calls_by_sport import search_team_id_by_name
from utils.functions import (
    structure_team_standing,
    format_last_matches,
    summarize_odds,
)
from common.constants import TIMEZONE
from common.lang_dicts import *
from common.common import get_lang, format_datetime
from common.keyboards import (
    build_back_to_home_page_button,
    build_back_button,
    build_user_keyboard,
)
from common.back_to_home_page import back_to_user_home_page_handler
from user.analyze_game.functions import summarize_injuries, summarize_matches
from user.analyze_game.common import (
    generate_gpt_analysis,
    ask_gpt_about_match,
    generate_stripe_payment_link,
    check_stripe_payment_webhook,
)
from user.analyze_game.keyboards import build_matches_keyboard, build_sports_keyboard
from start import start_command
from datetime import datetime, timedelta
import logging
import models
import json

log = logging.getLogger(__name__)

SPORT, GAME_INFO, PAY = range(3)


async def analyze_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        if not update.effective_user.id == 5558614802:
            await update.callback_query.answer(text=TEXTS[lang]["soon"], show_alert=True)
            return ConversationHandler.END

        keyboard = build_sports_keyboard(lang=lang, prefix="analyze")
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=False)[0])
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["choose_sport"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return SPORT


async def choose_sport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)

        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["plz_wait"],
        )

        if not update.callback_query.data.startswith("back"):
            sport = update.callback_query.data.replace("analyze_", "")
            now = datetime.now(TIMEZONE)
            with models.session_scope() as session:
                cached_fixtures = (
                    session.query(models.CachedFixture)
                    .filter(
                        models.CachedFixture.sport == sport,
                        models.CachedFixture.fixture_date >= now,
                        models.CachedFixture.fixture_date <= now + timedelta(days=1),
                    )
                    .all()
                )
                fixtures = [f.data for f in cached_fixtures]
            context.user_data["analyze_game_sport"] = sport
            context.user_data["analyze_game_fixtures"] = fixtures
        else:
            sport = context.user_data["analyze_game_sport"]
            fixtures = context.user_data["analyze_game_fixtures"]
        keyboard = build_matches_keyboard(matches=fixtures, lang=lang)
        keyboard.append(build_back_button(data="back_to_choose_sport", lang=lang))
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=False)[0])
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["request_game_info"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return GAME_INFO


back_to_choose_sport = analyze_game


async def change_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        page = int(update.callback_query.data.split("_")[-1])
        fixtures = context.user_data["analyze_game_fixtures"]
        keyboard = build_matches_keyboard(matches=fixtures, lang=lang, page=page)
        keyboard.append(build_back_button(data="back_to_choose_sport", lang=lang))
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=False)[0])
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["request_game_info"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return GAME_INFO


async def choose_from_todays_matches(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith("back"):
            fixture_id = int(update.callback_query.data.split("_")[-1])
            context.user_data["analyze_game_fixture_id"] = fixture_id
        else:
            fixture_id = context.user_data["analyze_game_fixture_id"]
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["plz_wait"],
        )
        fixture = None
        for fix in context.user_data["analyze_game_fixtures"]:
            if fix["fixture_id"] == fixture_id:
                fixture = fix
                break

        with models.session_scope() as session:
            h2h_obj = (
                session.query(models.CachedH2H)
                .filter_by(
                    fixture_id=fixture_id,
                    home_id=fixture["home_id"],
                    away_id=fixture["away_id"],
                    sport=context.user_data["analyze_game_sport"],
                )
                .first()
            )
            matches = h2h_obj.data if h2h_obj else []
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

        stripe_link = generate_stripe_payment_link(
            uid=update.effective_user.id, match_id=fixture_id
        )
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["analyze_game_ai_result"].format(
                format_datetime(datetime.fromisoformat(str(fixture["date"]))),
                fixture["league_name"],
                fixture["venue"],
                f"{fixture['home_name']} vs {fixture['away_name']}",
                stripe_link['url'],
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        context.user_data["match_info"] = {
            **fixture,
            "h2h": summarize_matches(matches),
        }
        return PAY


async def handle_match_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        sport = context.user_data["analyze_game_sport"]
        wait_msg = await update.message.reply_text(
            text=TEXTS[lang]["plz_wait"],
        )
        parsed = await ask_gpt_about_match(teams=update.message.text, sport=sport)
        try:
            parsed_json = json.loads(parsed)
        except Exception as e:
            log.error(f"Error while parsing teams names: {e}")
            await wait_msg.edit_text(
                text=TEXTS[lang]["no_upcoming_games"],
                reply_markup=InlineKeyboardMarkup(
                    build_back_to_home_page_button(lang=lang, is_admin=False)
                ),
            )
            return
        teams1 = await search_team_id_by_name(
            name=parsed_json["team1"].replace("-", " "), sport=sport
        )
        teams2 = await search_team_id_by_name(
            name=parsed_json["team2"].replace("-", " "), sport=sport
        )

        if not teams1 or not teams2:
            await update.message.reply_text(text=TEXTS[lang]["either_teams_wrong"])
            return

        for team1 in teams1:
            for team2 in teams2:
                with models.session_scope() as session:
                    h2h_obj = (
                        session.query(models.CachedH2H)
                        .filter_by(
                            home_id=(
                                team1["team"]["id"]
                                if sport == "football"
                                else team1["id"]
                            ),
                            away_id=(
                                team2["team"]["id"]
                                if sport == "football"
                                else team2["id"]
                            ),
                            sport=sport,
                        )
                        .first()
                    )
                    matches = h2h_obj.data if h2h_obj else []
                if matches:
                    fixture = matches[0]
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
                    teams = f"{fixture['home_name']} vs {fixture['away_name']}"

                    stripe_link = generate_stripe_payment_link(
                        uid=update.effective_user.id,
                        match_id=fixture["fixture_id"],
                    )

                    await wait_msg.edit_text(
                        text=TEXTS[lang]["analyze_game_ai_result"].format(
                            format_datetime(
                                datetime.fromisoformat(str(fixture["date"]))
                            ),
                            fixture["league_name"],
                            fixture["venue"],
                            teams,
                            stripe_link['url'],
                        ),
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                    context.user_data["match_info"] = {
                        **fixture,
                        "h2h": summarize_matches(matches),
                    }
                    return PAY
        await wait_msg.edit_text(
            text=TEXTS[lang]["no_upcoming_games"],
            reply_markup=build_user_keyboard(lang=lang),
        )
        context.user_data["analyze_game_fixtures"] = []
        context.user_data["match_info"] = {}
        return ConversationHandler.END


back_to_handle_match_input = choose_sport


async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)

        payment_ok = await check_stripe_payment_webhook(
            uid=update.effective_user.id,
            match_id=context.user_data["match_info"]["fixture_id"],
        )
        if not payment_ok:
            await update.callback_query.answer(
                text=TEXTS[lang]["payment_failed"],
                show_alert=True,
            )
            return

        sport = context.user_data["analyze_game_sport"]
        home_id = context.user_data["match_info"]["home_id"]
        away_id = context.user_data["match_info"]["away_id"]

        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["plz_wait"],
        )

        with models.session_scope() as session:
            home_last_obj = (
                session.query(models.CachedTeamResults)
                .filter_by(team_id=home_id, sport=sport)
                .first()
            )
            home_last = format_last_matches(
                matches=home_last_obj.data if home_last_obj else [],
                team_id=home_id,
                sport=sport,
            )
            away_last_obj = (
                session.query(models.CachedTeamResults)
                .filter_by(team_id=away_id, sport=sport)
                .first()
            )
            away_last = format_last_matches(
                matches=away_last_obj.data if away_last_obj else [],
                team_id=away_id,
                sport=sport,
            )
            home_rank_obj = (
                session.query(models.CachedStandings)
                .filter_by(
                    team_id=home_id,
                    league_id=context.user_data["match_info"]["league_id"],
                    season=context.user_data["match_info"]["season"],
                    sport=sport,
                )
                .first()
            )
            home_rank = structure_team_standing(
                data=home_rank_obj.data if home_rank_obj else None,
                sport=sport,
            )
            away_rank_obj = (
                session.query(models.CachedStandings)
                .filter_by(
                    team_id=away_id,
                    league_id=context.user_data["match_info"]["league_id"],
                    season=context.user_data["match_info"]["season"],
                    sport=sport,
                )
                .first()
            )
            away_rank = structure_team_standing(
                data=away_rank_obj.data if away_rank_obj else None,
                sport=sport,
            )
            # Injuries
            home_injuries_obj = (
                session.query(models.CachedInjuries)
                .filter_by(
                    team_id=home_id,
                    season=context.user_data["match_info"]["season"],
                    sport=sport,
                )
                .first()
            )
            home_injuries = home_injuries_obj.data if home_injuries_obj else []
            away_injuries_obj = (
                session.query(models.CachedInjuries)
                .filter_by(
                    team_id=away_id,
                    season=context.user_data["match_info"]["season"],
                    sport=sport,
                )
                .first()
            )
            away_injuries = away_injuries_obj.data if away_injuries_obj else []
            odds_obj = (
                session.query(models.CachedOdds)
                .filter_by(
                    fixture_id=context.user_data["match_info"]["fixture_id"],
                    sport=sport,
                )
                .first()
            )
            odds = odds_obj.data if odds_obj else None

        match_info = {
            "teams": f"{context.user_data['match_info']['home_name']} vs {context.user_data['match_info']['away_name']}",
            "date": context.user_data["match_info"]["date"],
            "league": context.user_data["match_info"]["league_name"],
            "venue": context.user_data["match_info"]["venue"],
            "home_name": context.user_data["match_info"]["home_name"],
            "away_name": context.user_data["match_info"]["away_name"],
            "h2h": context.user_data["match_info"]["h2h"],
            "home_last": home_last,
            "away_last": away_last,
            "home_rank": f"{home_rank} in league",
            "away_rank": f"{away_rank} in league",
            "home_inj": summarize_injuries(injuries=home_injuries, sport=sport),
            "away_inj": summarize_injuries(injuries=away_injuries, sport=sport),
            "odds": summarize_odds(odds),
        }

        gpt_analysis = await generate_gpt_analysis(match_info)
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["game_smart_analysis"].format(gpt_analysis),
            parse_mode=ParseMode.MARKDOWN,
        )
        context.user_data["analyze_game_fixtures"] = []
        context.user_data["match_info"] = {}
        return ConversationHandler.END


analyze_game_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            analyze_game,
            "^analyze_game$",
        )
    ],
    states={
        SPORT: [
            CallbackQueryHandler(
                choose_sport,
                r"^analyze_((hockey)|(american_football)|(basketball)|(football))$",
            )
        ],
        GAME_INFO: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=handle_match_input,
            ),
            CallbackQueryHandler(
                change_page,
                r"^analyze_match_page_",
            ),
            CallbackQueryHandler(
                choose_from_todays_matches,
                r"^analyze_match_",
            ),
        ],
        PAY: [
            CallbackQueryHandler(
                pay,
                r"^pay$",
            )
        ],
    },
    fallbacks=[
        back_to_user_home_page_handler,
        start_command,
        CallbackQueryHandler(
            back_to_handle_match_input,
            r"^back_to_handle_match_input$",
        ),
        CallbackQueryHandler(
            back_to_choose_sport,
            r"^back_to_choose_sport$",
        ),
    ],
    name="analyze_game_ai_conv",
    persistent=True,
)
