from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Chat
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    CommandHandler,
)
from groups.group_preferences.functions import *
from groups.group_preferences.constants import *
from groups.group_preferences.keyboards import *
from groups.group_preferences.lang_dicts import *
from common.common import get_lang
import models
from common.keyboards import build_back_button

LANG, DIALECT, SPORT, LEAGUE, CONFIRM = range(5)


async def start_group_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        lang = get_lang(update.effective_user.id)
        group_id = update.effective_chat.id
        is_admin = await check_admin(
            context=context,
            group_id=group_id,
            user_id=update.effective_user.id,
            lang=lang,
        )
        if not is_admin:
            return ConversationHandler.END

        with models.session_scope() as session:
            prefs = (
                session.query(models.GroupPreferences)
                .filter_by(group_id=group_id)
                .first()
            )
            if not prefs:
                prefs = models.GroupPreferences(group_id=group_id)
                session.add(prefs)
                session.commit()
            context.user_data["prefs"] = {
                "language": prefs.language,
                "dialect": prefs.dialect,
                "sports": prefs.sports or {},
            }
        keyboard = build_lang_kb()
        if update.message:
            await update.message.reply_text(
                text=TEXTS[lang]["choose_lang"],
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["choose_lang"],
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return LANG


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        lang = get_lang(update.effective_user.id)
        group_id = update.effective_chat.id
        is_admin = await check_admin(
            context=context,
            group_id=group_id,
            user_id=update.effective_user.id,
            lang=lang,
        )
        if not is_admin:
            return ConversationHandler.END
        if not update.callback_query.data.startswith("back"):
            l = update.callback_query.data.replace("set_lang_", "")
            context.user_data["prefs"]["language"] = l
        else:
            l = context.user_data["prefs"]["language"]
        keyboard = build_dialect_kb(lang=l)
        keyboard.append(build_back_button(data="back_to_set_language", lang=lang))
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["choose_dialect"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return DIALECT


back_to_set_language = start_group_settings


async def set_dialect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        lang = get_lang(update.effective_user.id)
        dialect = update.callback_query.data.replace("set_dialect_", "")
        context.user_data["prefs"]["dialect"] = dialect
        sports: dict = context.user_data["prefs"].get("sports", {})
        keyboard = build_sports_kb(selected=sports.keys(), lang=lang)
        keyboard.append(build_back_button(data="back_to_set_dialect", lang=lang))
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["choose_sports"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return SPORT


back_to_set_dialect = set_language


async def toggle_sport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        lang = get_lang(update.effective_user.id)
        sport = update.callback_query.data.replace("toggle_sport_", "")
        sports: dict = context.user_data["prefs"].setdefault("sports", {})
        if sport in sports:
            del sports[sport]
        else:
            sports[sport] = []
        keyboard = build_sports_kb(selected=sports.keys(), lang=lang)
        keyboard.append(build_back_button(data="back_to_set_dialect", lang=lang))
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["choose_sports"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return SPORT


async def sports_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        lang = get_lang(update.effective_user.id)
        sports: dict = context.user_data["prefs"]["sports"]
        context.user_data["league_sport_iter"] = None
        if not sports:
            return await confirm_settings(update, context)
        context.user_data["league_sport_iter"] = iter(sports.keys())
        context.user_data["league_current_sport"] = next(
            context.user_data["league_sport_iter"]
        )
        sport = context.user_data["league_current_sport"]
        keyboard = build_leagues_kb(
            sport=sport,
            lang=lang,
            selected_ids=sports[sport],
        )
        keyboard.append(build_back_button(data="back_to_choose_sports", lang=lang))
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["choose_leagues"].format(SPORTS[sport][lang]),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return LEAGUE


back_to_choose_sports = set_dialect


async def toggle_league(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        lang = get_lang(update.effective_user.id)
        data = update.callback_query.data.split("_")
        sport = data[2]
        league_id = int(data[-1])
        leagues: list = context.user_data["prefs"]["sports"].setdefault(sport, [])
        if league_id in leagues:
            leagues.remove(league_id)
        else:
            leagues.append(league_id)
        keyboard = build_leagues_kb(
            sport=sport,
            lang=lang,
            selected_ids=leagues,
        )
        keyboard.append(build_back_button(data="back_to_choose_sports", lang=lang))
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["choose_leagues"].format(SPORTS[sport][lang]),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return LEAGUE


async def leagues_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        lang = get_lang(update.effective_user.id)
        sport_iter = context.user_data["league_sport_iter"]
        if not sport_iter:
            return await confirm_settings(update, context)
        try:
            sport = next(sport_iter)
            context.user_data["league_current_sport"] = sport
            keyboard = build_leagues_kb(
                sport=sport,
                lang=lang,
                selected_ids=context.user_data["prefs"]["sports"][sport],
            )
            keyboard.append(build_back_button(data="back_to_choose_sports", lang=lang))
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["choose_leagues"].format(SPORTS[sport][lang]),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return LEAGUE
        except StopIteration:
            return await confirm_settings(update, context)


async def confirm_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        lang = get_lang(update.effective_user.id)
        prefs = context.user_data["prefs"]
        await update.callback_query.edit_message_text(
            text=construct_prefs_summary(prefs=prefs, lang=lang),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=BUTTONS[lang]["save"],
                            callback_data="save_settings",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=BUTTONS[lang]["cancel"],
                            callback_data="cancel_settings",
                        )
                    ],
                    build_back_button(data="back_to_choose_leagues", lang=lang),
                ],
            ),
        )
        return CONFIRM


back_to_choose_leagues = sports_done


async def save_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        lang = get_lang(update.effective_user.id)
        group_id = update.effective_chat.id
        with models.session_scope() as session:
            prefs = (
                session.query(models.GroupPreferences)
                .filter_by(group_id=group_id)
                .first()
            )
            if not prefs:
                prefs = models.GroupPreferences(group_id=group_id)
                session.add(prefs)
                session.commit()
            for k, v in context.user_data["prefs"].items():
                setattr(prefs, k, v)
            session.commit()

        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["prefs_save_success"]
        )
        return ConversationHandler.END


async def cancel_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        lang = get_lang(update.effective_user.id)
        if update.message:
            await update.message.reply_text(text=TEXTS[lang]["operation_canceled"])
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["operation_canceled"]
            )
        return ConversationHandler.END


group_settings_handler = ConversationHandler(
    allow_reentry=True,
    entry_points=[
        CommandHandler(
            "settings",
            start_group_settings,
        )
    ],
    states={
        LANG: [
            CallbackQueryHandler(
                set_language,
                pattern=r"^set_lang_",
            )
        ],
        DIALECT: [
            CallbackQueryHandler(
                set_dialect,
                pattern=r"^set_dialect_",
            )
        ],
        SPORT: [
            CallbackQueryHandler(
                toggle_sport,
                pattern=r"^toggle_sport_",
            ),
            CallbackQueryHandler(
                sports_done,
                pattern=r"^sports_done$",
            ),
        ],
        LEAGUE: [
            CallbackQueryHandler(
                toggle_league,
                pattern=r"^toggle_league_",
            ),
            CallbackQueryHandler(
                leagues_done,
                pattern=r"^leagues_done_",
            ),
        ],
        CONFIRM: [
            CallbackQueryHandler(
                save_settings,
                pattern=r"^save_settings$",
            ),
            CallbackQueryHandler(
                cancel_settings,
                pattern=r"^cancel_settings$",
            ),
        ],
    },
    fallbacks=[
        CommandHandler(
            "cancel",
            cancel_settings,
        ),
        CallbackQueryHandler(back_to_choose_leagues, r"^back_to_choose_leagues$"),
        CallbackQueryHandler(back_to_choose_sports, r"^back_to_choose_sports$"),
        CallbackQueryHandler(back_to_set_dialect, r"^back_to_set_dialect$"),
        CallbackQueryHandler(back_to_set_language, r"^back_to_set_language$"),
    ],
    name="group_settings_conv",
    persistent=True,
)
