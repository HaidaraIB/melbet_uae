from telegram import Update, Chat, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler
import models
from common.common import get_lang
from common.lang_dicts import *
from common.back_to_home_page import back_to_user_home_page_handler
from common.keyboards import (
    build_keyboard,
    build_back_button,
    build_back_to_home_page_button,
)
from start import start_command


TRANSACTION = range(1)


async def my_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            transactions = (
                s.query(models.Transaction)
                .filter_by(user_id=update.effective_user.id)
                .limit(20)
                .all()
            )
            keyboard = build_keyboard(
                columns=3,
                texts=[t.id for t in transactions],
                buttons_data=[f"my_transaction_{t.id}" for t in transactions],
            )
            keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=False)[0]
            )
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["choose_my_transaction"],
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return TRANSACTION


async def choose_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        transaction_id = int(update.callback_query.data.split("_")[-1])
        back_buttons = [
            build_back_button(data="back_to_choose_transaction"),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        with models.session_scope() as s:
            transaction = s.get(models.Transaction, transaction_id)
            await update.callback_query.edit_message_text(
                text=transaction.stringify(lang=lang),
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )


back_to_choose_transaction = my_transactions


my_transactions_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            my_transactions,
            r"^my_transactions$",
        ),
    ],
    states={
        TRANSACTION: [
            CallbackQueryHandler(choose_transaction, r"^my_transaction_[0-9]+$")
        ],
    },
    fallbacks=[
        back_to_user_home_page_handler,
        start_command,
        CallbackQueryHandler(
            back_to_choose_transaction, r"^back_to_choose_transaction$"
        ),
    ],
)
