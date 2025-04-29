from telegram import Update, Chat
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler
from common.decorators import check_if_user_member_decorator
from common.keyboards import build_user_keyboard, build_admin_keyboard
from common.constants import *
from common.lang_dicts import *
from common.common import get_lang
from custom_filters import Admin


@check_if_user_member_decorator
async def back_to_user_home_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_user_keyboard(lang),
        )
        return ConversationHandler.END


async def back_to_admin_home_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.edit_message_text(
            text=HOME_PAGE_TEXT,
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


back_to_user_home_page_handler = CallbackQueryHandler(
    back_to_user_home_page, "^back_to_user_home_page$"
)
back_to_admin_home_page_handler = CallbackQueryHandler(
    back_to_admin_home_page, "^back_to_admin_home_page$"
)
