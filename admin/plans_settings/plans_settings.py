from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import models
from custom_filters import Admin
from common.keyboards import (
    build_back_button,
    build_back_to_home_page_button,
    build_admin_keyboard,
)
from common.back_to_home_page import back_to_admin_home_page_handler
from start import admin_command
from client.client_calls.common import openai
from Config import Config
from openai.types.chat_model import ChatModel
PLAN, FIELD, VALUE = range(3)


async def gpt_translate(text: str, target_lang: str):
    translated_text = (
        (
            await openai.chat.completions.create(
                model=Config.GPT_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": f"Translate this {text} to {target_lang} and only reply with the translated text",
                    }
                ],
                temperature=0.3,
            )
        )
        .choices[0]
        .message.content.strip()
    )
    return translated_text


async def plans_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        with models.session_scope() as session:
            plans = session.query(models.Plan).all()
            keyboard = [
                [
                    InlineKeyboardButton(
                        text=p.name_ar,
                        callback_data=f"plan_{p.code}",
                    )
                ]
                for p in plans
            ]
            keyboard.append(build_back_to_home_page_button()[0])
        await update.callback_query.edit_message_text(
            text="اختر خطة للتعديل:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return PLAN


async def choose_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data.startswith("back"):
            code = update.callback_query.data.split("_")[1]
            context.user_data["plan_code"] = code
        keyboard = [
            [
                InlineKeyboardButton(
                    "✏️ تعديل الوصف",
                    callback_data="edit_plan_details",
                )
            ],
            [
                InlineKeyboardButton(
                    "💲 تعديل السعر",
                    callback_data="edit_plan_price",
                )
            ],
            build_back_button(data="back_to_choose_plan"),
            build_back_to_home_page_button()[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر ما تريد تعديله:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return FIELD


back_to_choose_plan = plans_settings


async def choose_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data.startswith("back"):
            field = update.callback_query.data
            context.user_data["edit_field"] = field
        else:
            field = context.user_data["edit_field"]
        back_buttons = [
            build_back_button(data="back_to_choose_field"),
            build_back_to_home_page_button()[0],
        ]
        if field == "edit_plan_details":
            text = "أرسل النص الجديد للوصف (عربي أو إنجليزي)."
        elif field == "edit_plan_price":
            text = "أرسل النص الجديد للسعر (عربي أو إنجليزي)."
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return VALUE


back_to_choose_field = choose_plan


async def get_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        with models.session_scope() as session:
            code = context.user_data["plan_code"]
            field = context.user_data["edit_field"]
            plan = session.query(models.Plan).filter_by(code=code).first()
            value = update.message.text.strip()
            is_arabic = any("\u0600" <= c <= "\u06ff" for c in value)

            if field == "edit_plan_details":
                if is_arabic:
                    plan.details_ar = value
                    plan.details_en = await gpt_translate(text=value, target_lang="en")
                else:
                    plan.details_en = value
                    plan.details_ar = await gpt_translate(text=value, target_lang="ar")
            elif field == "edit_plan_price":
                plan.price = value
            session.commit()
        await update.message.reply_text(
            text="✅ تم حفظ التعديل وتحديث الترجمة تلقائيًا.",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


plans_settings_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            plans_settings,
            r"^plans_settings$",
        )
    ],
    states={
        PLAN: [
            CallbackQueryHandler(
                choose_plan,
                pattern=r"^plan_",
            )
        ],
        FIELD: [
            CallbackQueryHandler(
                choose_field,
                pattern=r"^edit_plan",
            )
        ],
        VALUE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_value,
            )
        ],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        CallbackQueryHandler(back_to_choose_field, r"^back_to_choose_field$"),
        CallbackQueryHandler(back_to_choose_plan, r"^back_to_choose_plan$"),
    ],
)
