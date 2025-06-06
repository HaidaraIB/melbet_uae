from telegram import InlineKeyboardMarkup, Update, Chat
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from common.keyboards import (
    build_back_to_home_page_button,
    build_back_button,
    build_admin_keyboard,
)
from common.back_to_home_page import back_to_admin_home_page_handler
from admin.prompt_settings.common import prompt_panel
from custom_filters import Admin
from start import admin_command
import models


PROMPT_TYPE, NEW_VAL = range(2)


async def prompt_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = prompt_panel()
        keyboard.append(build_back_to_home_page_button()[0])
        await update.callback_query.edit_message_text(
            text="اختر نوع البرومبت لتعديله:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return PROMPT_TYPE


async def choose_prompt_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        title_map = {
            "monitor": "المراقبة",
            "session": "الجلسات",
            "manager": "المدير",
            "change_account": "تغيير الحساب",
            "deposit": "الإيداع",
            "withdraw": "السحب",
            "security_messages": "رسائل الأمان",
            "promotional": "الترويج",
            "match_summary": "ملخص المباريات",
            "voucher": "القسائم",
            "dp_wd_instructions": "تعليمات الإيداع والسحب"
        }
        back_buttons = [
            build_back_button(data="back_to_choose_prompt_type"),
            build_back_to_home_page_button()[0],
        ]
        if not update.callback_query.data.startswith("back"):
            prompt_type = update.callback_query.data.replace("edit_prompt_", "")
            context.user_data["prompt_type"] = prompt_type
        else:
            prompt_type = context.user_data["prompt_type"]

        with models.session_scope() as s:
            setting = s.get(models.Setting, f"gpt_prompt_{prompt_type}")
            current_prompt = ""
            if setting:
                current_prompt = setting.value

        await update.callback_query.edit_message_text(
            text=(
                f"أرسل الآن البرومبت الجديد لـ {title_map[prompt_type]}\n"
                f"البرومبت الحالي:\n"
                f"<code>{current_prompt}</code>"
            ),
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return NEW_VAL


back_to_choose_prompt_type = prompt_settings


async def get_new_val(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        prompt_type = context.user_data.get("prompt_type")
        text = update.message.text.strip()
        with models.session_scope() as s:
            setting = s.get(models.Setting, f"gpt_prompt_{prompt_type}")
            if setting:
                setting.value = text
            else:
                s.add(models.Setting(key=f"gpt_prompt_{prompt_type}", value=text))
            s.commit()
        await update.message.reply_text(
            text="تم تحديث البرومبت بنجاح ✅",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


prompt_settings_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            prompt_settings,
            r"^prompt_settings$",
        )
    ],
    states={
        PROMPT_TYPE: [
            CallbackQueryHandler(
                choose_prompt_type,
                r"^edit_prompt_",
            )
        ],
        NEW_VAL: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_new_val,
            )
        ],
    },
    fallbacks=[
        admin_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(
            back_to_choose_prompt_type, "^back_to_choose_prompt_type$"
        ),
    ],
)
