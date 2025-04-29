from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ChatMemberStatus
from common.keyboards import build_user_keyboard
from common.common import get_lang
from common.lang_dicts import *
from Config import Config


async def check_if_user_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        chat_id=Config.FORCE_JOIN_CHANNEL_ID,
        user_id=update.effective_user.id,
    )
    if chat_member.status == ChatMemberStatus.LEFT:
        lang = get_lang(update.effective_user.id)
        markup = InlineKeyboardMarkup.from_column(
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["bot_channel"],
                    url=Config.FORCE_JOIN_CHANNEL_LINK,
                ),
                InlineKeyboardButton(
                    text=BUTTONS[lang]["check_joined"],
                    callback_data="check_joined",
                ),
            ]
        )
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["force_join_msg"],
                reply_markup=markup,
            )
        else:
            await update.message.reply_text(
                text=TEXTS[lang]["force_join_msg"],
                reply_markup=markup,
            )
        return False
    return True


async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_memeber = await context.bot.get_chat_member(
        chat_id=Config.FORCE_JOIN_CHANNEL_ID, user_id=update.effective_user.id
    )
    lang = get_lang(update.effective_user.id)
    if chat_memeber.status == ChatMemberStatus.LEFT:
        await update.callback_query.answer(
            text=TEXTS[lang]["join_first_answer"],
            show_alert=True,
        )
        return
    await update.callback_query.edit_message_text(
        text=TEXTS[lang]["welcome_msg"],
        reply_markup=build_user_keyboard(lang),
    )


check_joined_handler = CallbackQueryHandler(
    callback=check_joined,
    pattern="^check_joined$",
)
