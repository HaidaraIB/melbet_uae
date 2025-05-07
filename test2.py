from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import models
from Config import Config

def prompt_panel():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🛡 برومبت المراقبة", callback_data="edit_prompt_monitor"
                )
            ],
            [
                InlineKeyboardButton(
                    "🤖 برومبت الجلسات", callback_data="edit_prompt_session"
                )
            ],
            [
                InlineKeyboardButton(
                    "👤 برومبت المدير", callback_data="edit_prompt_manager"
                )
            ],
            [
                InlineKeyboardButton(
                    "✏️ برومبت تغيير الحساب", callback_data="edit_prompt_change_account"
                )
            ],
        ]
    )


from telegram.ext import CommandHandler


async def prompt_panel_command(update, context):
    if update.effective_user.id != Config.ADMIN_ID:
        return
    await update.message.reply_text(
        "اختر نوع البرومبت لتعديله:", reply_markup=prompt_panel()
    )


from telegram.ext import CallbackQueryHandler, ConversationHandler

SELECTING_PROMPT, TYPING_PROMPT = range(2)


async def prompt_button(update, context):
    query = update.callback_query
    await query.answer()
    prompt_type = query.data.replace("edit_prompt_", "")
    context.user_data["prompt_type"] = prompt_type
    title_map = {
        "monitor": "برومبت المراقبة",
        "session": "برومبت الجلسات",
        "manager": "برومبت المدير",
        "change_account": "برومبت تغيير الحساب",
    }
    await query.message.reply_text(
        f"أرسل الآن البرومبت الجديد لـ {title_map[prompt_type]}:"
    )
    return TYPING_PROMPT


async def save_prompt(update, context):
    prompt_type = context.user_data.get("prompt_type")
    text = update.message.text.strip()
    db_keys = {
        "monitor": "gpt_prompt_monitor",
        "session": "gpt_prompt_session",
        "manager": "gpt_prompt_manager",
        "change_account": "gpt_prompt_change_account",
    }
    key = db_keys.get(prompt_type)
    if key:
        with models.session_scope() as s:
            setting = s.get(models.Setting, key)
            if setting:
                setting.value = text
            else:
                s.add(models.Setting(key=key, value=text))
                s.commit()
            await update.message.reply_text("✅ تم تحديث البرومبت بنجاح.")
        return ConversationHandler.END


from telegram.ext import ApplicationBuilder, MessageHandler, filters

application = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()
application.add_handler(CommandHandler("prompt_panel", prompt_panel_command))
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(prompt_button, pattern=r"^edit_prompt_")],
    states={
        TYPING_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_prompt)]
    },
    fallbacks=[],
)
application.add_handler(conv_handler)
