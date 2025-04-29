from telegram import Chat, Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler
from common.keyboards import build_back_to_home_page_button
from admin.admin_settings.common import build_admin_settings_keyboard
from custom_filters import Admin


async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = build_admin_settings_keyboard()
        keyboard.append(build_back_to_home_page_button()[0])
        await update.callback_query.edit_message_text(
            text="إعدادات الآدمن 🪄",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END


admin_settings_handler = CallbackQueryHandler(
    admin_settings,
    "^admin_settings$|^back_to_admin_settings$",
)
