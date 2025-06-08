from telegram import Update, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)
from telegram.constants import ParseMode
import json
from user.analyze_game.api_calls import (
    search_team_id_by_name,
    get_h2h_by_sport,
    get_team_injuries_by_sport,
    get_team_standing_by_sport,
    get_last_matches_by_sport,
    get_fixture_odds_by_sport,
    get_fixtures_by_sport,
)
from utils.functions import filter_fixtures
from common.lang_dicts import *
from common.common import get_lang, format_datetime
from common.keyboards import (
    build_back_to_home_page_button,
    build_back_button,
    build_user_keyboard,
)
from common.back_to_home_page import back_to_user_home_page_handler
from start import start_command
from datetime import datetime
import logging
from user.analyze_game.common import (
    summarize_injuries,
    summarize_matches,
    summarize_odds,
    generate_gpt_analysis,
    build_matches_keyboard,
    ask_gpt_about_match,
    build_sports_keyboard,
)

log = logging.getLogger(__name__)

SPORT, GAME_INFO, PAY = range(3)


async def analyze_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
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
            fixtures = await get_fixtures_by_sport(sport=sport)
            fixtures = filter_fixtures(fixtures=fixtures, sport=sport)
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

        h2h = f"{fixture['home_id']}-{fixture['away_id']}"
        teams = f"{fixture['home_name']} vs {fixture['away_name']}"
        matches = await get_h2h_by_sport(
            h2h=h2h,
            sport=context.user_data["analyze_game_sport"],
        )
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
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["analyze_game_ai_result"].format(
                format_datetime(datetime.fromisoformat(str(fixture["date"]))),
                fixture["league_name"],
                fixture["venue"],
                teams,
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
                matches = await get_h2h_by_sport(
                    h2h=(
                        f"{team1['team']['id']}-{team2['team']['id']}"
                        if sport == "football"
                        else f"{team1['id']}-{team2['id']}"
                    ),
                    sport=sport,
                )
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
                    await wait_msg.edit_text(
                        text=TEXTS[lang]["analyze_game_ai_result"].format(
                            format_datetime(
                                datetime.fromisoformat(str(fixture["date"]))
                            ),
                            fixture["league_name"],
                            fixture["venue"],
                            teams,
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
        sport = context.user_data["analyze_game_sport"]

        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["plz_wait"],
        )

        home_last = await get_last_matches_by_sport(
            team_id=context.user_data["match_info"]["home_id"],
            sport=sport,
            season=context.user_data["match_info"]["season"],
        )
        away_last = await get_last_matches_by_sport(
            team_id=context.user_data["match_info"]["away_id"],
            sport=sport,
            season=context.user_data["match_info"]["season"],
        )

        home_rank = await get_team_standing_by_sport(
            team_id=context.user_data["match_info"]["home_id"],
            league_id=context.user_data["match_info"]["league_id"],
            season=context.user_data["match_info"]["season"],
            sport=sport,
        )
        away_rank = await get_team_standing_by_sport(
            team_id=context.user_data["match_info"]["away_id"],
            league_id=context.user_data["match_info"]["league_id"],
            season=context.user_data["match_info"]["season"],
            sport=sport,
        )
        home_injuries = await get_team_injuries_by_sport(
            team_id=context.user_data["match_info"]["home_id"],
            season=context.user_data["match_info"]["season"],
            sport=sport,
        )
        away_injuries = await get_team_injuries_by_sport(
            team_id=context.user_data["match_info"]["away_id"],
            season=context.user_data["match_info"]["season"],
            sport=sport,
        )

        odds = await get_fixture_odds_by_sport(
            fixture_id=context.user_data["match_info"]["fixture_id"], sport=sport
        )

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
