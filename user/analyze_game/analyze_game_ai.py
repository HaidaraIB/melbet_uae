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
from client.client_calls.common import openai
from Config import Config
from user.analyze_game.api_calls import (
    search_team_id_by_name,
    get_h2h,
    get_team_injuries,
    get_team_standing,
    get_last_matches,
    get_fixture_odds,
    BASE_URL,
)
from common.lang_dicts import *
from common.common import get_lang, format_datetime
from common.keyboards import build_back_to_home_page_button, build_back_button
from common.back_to_home_page import back_to_user_home_page_handler
from start import start_command
from datetime import datetime
import logging
from user.analyze_game.common import (
    summarize_injuries,
    summarize_matches,
    summarize_odds,
    generate_gpt_analysis,
)

log = logging.getLogger(__name__)

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
            name=parsed_json["team1"].replace("-", " ")
        )
        teams2 = await search_team_id_by_name(
            name=parsed_json["team2"].replace("-", " ")
        )

        if not teams1 or not teams2:
            await update.message.reply_text(text=TEXTS[lang]["either_teams_wrong"])
            return

        for team1 in teams1:
            for team2 in teams2:
                matches = await get_h2h(
                    h2h=f"{team1['team']['id']}-{team2['team']['id']}"
                )
                if matches['new']:
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
                            format_datetime(
                                datetime.fromisoformat(
                                    matches["new"][0]["fixture"]["date"]
                                )
                            ),
                            matches["new"][0]["league"]["name"],
                            matches["new"][0]["fixture"]["venue"]["name"],
                            f"{matches['new'][0]['teams']['home']['name']} vs {matches['new'][0]['teams']['away']['name']}",
                        ),
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                    context.user_data["match_info"] = {
                        "teams": f"{team1['team']['name']} vs {team2['team']['name']}",
                        "date": matches["new"][0]["fixture"]["date"],
                        "league": matches["new"][0]["league"],
                        "venue": matches["new"][0]["fixture"]["venue"]["name"],
                        "team1_name": team1["team"]["name"],
                        "team2_name": team2["team"]["name"],
                        "team1_id": team1["team"]["id"],
                        "team2_id": team2["team"]["id"],
                        "h2h": summarize_matches(matches["finished"]),
                        "fixture_id": matches["new"][0]["fixture"]["id"],
                    }
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

        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["plz_wait"],
        )

        team1_last = await get_last_matches(
            team_id=context.user_data["match_info"]["team1_id"]
        )
        team2_last = await get_last_matches(
            team_id=context.user_data["match_info"]["team2_id"]
        )

        team1_rank = await get_team_standing(
            team_id=context.user_data["match_info"]["team1_id"],
            league_id=context.user_data["match_info"]["league"]["id"],
            season=context.user_data["match_info"]["league"]["season"],
        )
        team2_rank = await get_team_standing(
            team_id=context.user_data["match_info"]["team2_id"],
            league_id=context.user_data["match_info"]["league"]["id"],
            season=context.user_data["match_info"]["league"]["season"],
        )
        team1_injuries = await get_team_injuries(
            team_id=context.user_data["match_info"]["team1_id"],
            season=context.user_data["match_info"]["league"]["season"],
        )
        team2_injuries = await get_team_injuries(
            team_id=context.user_data["match_info"]["team2_id"],
            season=context.user_data["match_info"]["league"]["season"],
        )

        odds = await get_fixture_odds(
            fixture_id=context.user_data["match_info"]["fixture_id"]
        )

        match_info = {
            "teams": context.user_data["match_info"]["teams"],
            "date": context.user_data["match_info"]["date"],
            "league": context.user_data["match_info"]["league"],
            "venue": context.user_data["match_info"]["venue"],
            "team1_name": context.user_data["match_info"]["team1_name"],
            "team2_name": context.user_data["match_info"]["team2_name"],
            "h2h": context.user_data["match_info"]["h2h"],
            "team1_last": summarize_matches(team1_last),
            "team2_last": summarize_matches(team2_last),
            "team1_rank": f"{team1_rank} in league",
            "team2_rank": f"{team2_rank} in league",
            "team1_inj": summarize_injuries(team1_injuries),
            "team2_inj": summarize_injuries(team2_injuries),
            "odds": summarize_odds(odds),
        }

        gpt_analysis = await generate_gpt_analysis(match_info)
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["game_smart_analysis"].format(gpt_analysis),
            parse_mode=ParseMode.MARKDOWN,
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
    name="analyze_game_ai_conv",
    persistent=True,
)
