from telegram import (
    Chat,
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButtonRequestUsers,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from common.back_to_home_page import back_to_admin_home_page_handler
from common.keyboards import build_admin_keyboard
from common.constants import *
from custom_filters import Admin
from admin.admin_settings.admin_settings import admin_settings_handler
from start import admin_command
import models

NEW_ADMIN_ID = 0


async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.answer()
        await update.callback_query.delete_message()
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                "اختر حساب الآدمن الذي تريد إضافته بالضغط على الزر أدناه\n\n"
                "يمكنك إرسال الid برسالة أيضاً\n\n"
                "أو إلغاء العملية بالضغط على /admin."
            ),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(
                            text="اختيار حساب آدمن",
                            request_users=KeyboardButtonRequestUsers(
                                request_id=4, user_is_bot=False
                            ),
                        )
                    ]
                ],
                resize_keyboard=True,
            ),
        )
        return NEW_ADMIN_ID


async def new_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if update.effective_message.users_shared:
            admin_id = update.effective_message.users_shared.users[0].user_id
        else:
            admin_id = int(update.message.text)

        with models.session_scope() as s:
            admin = s.get(models.User, admin_id)

            if not admin:
                admin_chat = await context.bot.get_chat(chat_id=admin_id)
                admin = models.User(
                    user_id=admin_chat.id,
                    username=admin_chat.username if admin_chat.username else "",
                    name=admin_chat.full_name,
                    is_admin=True,
                )
                s.add(admin)
            else:
                admin.is_admin = True

        await update.message.reply_text(
            text="تمت إضافة الآدمن بنجاح ✅",
            reply_markup=ReplyKeyboardRemove(),
        )
        await update.message.reply_text(
            text=HOME_PAGE_TEXT,
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


add_admin_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=add_admin,
            pattern="^add_admin$",
        ),
    ],
    states={
        NEW_ADMIN_ID: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=new_admin_id,
            ),
            MessageHandler(
                filters=filters.StatusUpdate.USERS_SHARED,
                callback=new_admin_id,
            ),
        ]
    },
    fallbacks=[
        admin_settings_handler,
        admin_command,
        back_to_admin_home_page_handler,
    ],
)
