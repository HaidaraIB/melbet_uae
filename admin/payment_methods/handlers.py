from telegram import Chat, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from custom_filters import Admin
from admin.payment_methods.keyboards import (
    build_payemnt_methods_settings_keyboard,
    build_payemnt_method_types_keyboard,
    build_payment_method_modes_keyboard,
)
from common.back_to_home_page import back_to_admin_home_page_handler
from start import admin_command
from common.keyboards import (
    build_back_button,
    build_back_to_home_page_button,
    build_admin_keyboard,
)
from sqlalchemy import func, or_
import models

NAME, DETAILS, TYPE, MODE = range(4)


async def open_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = build_payemnt_methods_settings_keyboard()
        keyboard.append(build_back_to_home_page_button()[0])
        await update.callback_query.edit_message_text(
            text="إعدادات وسائل الدفع",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END


async def add_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        back_buttons = [
            build_back_button(data="back_to_payment_method_settings"),
            build_back_to_home_page_button()[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل اسم وسيلة الدفع",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return NAME


back_to_payment_method_settings = open_settings


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        back_buttons = [
            build_back_button(data="back_to_get_name"),
            build_back_to_home_page_button()[0],
        ]
        if update.message:
            name = update.message.text
            with models.session_scope() as s:

                payment_method = (
                    s.query(models.PaymentMethod)
                    .filter(
                        or_(
                            func.lower(models.PaymentMethod.name).contains(
                                name.lower()
                            ),
                            func.lower(name).contains(
                                func.lower(models.PaymentMethod.name)
                            ),
                        )
                    )
                    .first()
                )
                if payment_method:
                    await update.message.reply_text(
                        text=f"<b>{name}</b> مضافة بالفعل ❗️"
                    )
                    return
            context.user_data["payment_method_name"] = name
            await update.message.reply_text(
                text="أرسل تفاصيل وسيلة الدفع مثل رقم الحساب البنكي و رقم IBAN",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أرسل تفاصيل وسيلة الدفع مثل رقم الحساب البنكي و رقم IBAN",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return DETAILS


back_to_get_name = add_payment_method


async def get_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = [
            *build_payemnt_method_types_keyboard(),
            build_back_button(data="back_to_get_details"),
            build_back_to_home_page_button()[0],
        ]
        if update.message:
            details = update.message.text
            context.user_data["payment_method_details"] = details
            await update.message.reply_text(
                text="اختر نوع هذه الوسيلة", reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.callback_query.edit_message_text(
                text="اختر نوع هذه الوسيلة", reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return TYPE


back_to_get_details = get_name


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = [
            *build_payment_method_modes_keyboard(),
            build_back_button(data="back_to_choose_type"),
            build_back_to_home_page_button()[0],
        ]
        if not update.callback_query.data.startswith("start"):
            t = update.callback_query.data.replace("_payment_method", "")
            context.user_data["payment_method_type"] = t

        await update.callback_query.edit_message_text(
            text="اختر نمط معالجة الإيداع",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return MODE


back_to_choose_type = get_details


async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        mode = update.callback_query.data.replace("_payment_method", "")
        with models.session_scope() as s:
            payment_method = models.PaymentMethod(
                name=context.user_data["payment_method_name"],
                details=context.user_data["payment_method_details"],
                type=context.user_data["payment_method_type"],
                mode=mode,
            )
            s.add(payment_method)
            s.commit()
        await update.callback_query.edit_message_text(
            text="تمت إضافة وسيلة الدفع بنجاح ✅",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


payment_method_settings_handler = CallbackQueryHandler(
    open_settings,
    r"^payment_method_settings$",
)

add_payment_method_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            add_payment_method,
            r"^add_payemnt_method$",
        ),
    ],
    states={
        NAME: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_name,
            ),
        ],
        DETAILS: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_details,
            ),
        ],
        TYPE: [
            CallbackQueryHandler(
                choose_type,
                r"^((withdraw)|(deposit)|(both))_payment_method$",
            ),
        ],
        MODE: [
            CallbackQueryHandler(
                choose_mode,
                r"^((auto)|(manual))_payment_method$",
            )
        ],
    },
    fallbacks=[
        admin_command,
        back_to_admin_home_page_handler,
        payment_method_settings_handler,
        CallbackQueryHandler(
            back_to_payment_method_settings, r"^$back_to_payment_method_settings"
        ),
        CallbackQueryHandler(back_to_get_name, r"^back_to_get_name$"),
        CallbackQueryHandler(back_to_get_details, r"^back_to_get_details$"),
        CallbackQueryHandler(back_to_choose_type, r"^back_to_choose_type$"),
    ],
)
