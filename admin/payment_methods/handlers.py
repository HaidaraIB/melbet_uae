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
    build_country_selection_keyboard,
    build_edit_fields_keyboard,
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

NAME, COUNTRY, DETAILS, TYPE, MODE = range(5)


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
        keyboard = [
            *build_country_selection_keyboard(),
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
                text="اختر الدولة الخاصة بوسيلة الدفع",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text="اختر الدولة الخاصة بوسيلة الدفع",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return COUNTRY


back_to_get_name = add_payment_method


async def choose_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data.startswith("back"):
            country = update.callback_query.data.replace("country_", "")
            context.user_data["payment_method_country"] = country
        back_buttons = [
            build_back_button(data="back_to_get_country"),
            build_back_to_home_page_button()[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل تفاصيل وسيلة الدفع مثل رقم الحساب البنكي و رقم IBAN",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return DETAILS


back_to_get_country = get_name


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


back_to_get_details = choose_country


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
                country=context.user_data.get("payment_method_country", "uae"),
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
        COUNTRY: [
            CallbackQueryHandler(
                choose_country,
                r"^country_(uae|syria)$",
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
        CallbackQueryHandler(back_to_get_country, r"^back_to_get_country$"),
        CallbackQueryHandler(back_to_get_details, r"^back_to_get_details$"),
        CallbackQueryHandler(back_to_choose_type, r"^back_to_choose_type$"),
    ],
)


(
    SELECT_COUNTRY,
    SELECT_METHOD,
    CHOOSE_FIELD,
    EDIT_NAME,
    EDIT_DETAILS,
    EDIT_TYPE,
    EDIT_MODE,
    EDIT_COUNTRY,
    CONFIRM_UPDATE,
) = range(9)


async def start_update_payment_method(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    keyboard = [
        *build_country_selection_keyboard(),
        build_back_button(data="back_to_payment_method_settings"),
        build_back_to_home_page_button()[0],
    ]
    await update.callback_query.edit_message_text(
        text="اختر الدولة لتعديل وسائل الدفع",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return SELECT_COUNTRY


async def select_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country = update.callback_query.data.replace("country_", "")
    context.user_data["update_country"] = country
    with models.session_scope() as s:
        methods = s.query(models.PaymentMethod).filter_by(country=country).all()
        if not methods:
            await update.callback_query.answer(
                text=f"لا توجد وسائل دفع مضافة لهذه الدولة ({country})",
                show_alert=True,
            )
            return
        method_buttons = [
            [
                InlineKeyboardButton(
                    text=m.name,
                    callback_data=f"update_method_{m.id}",
                )
            ]
            for m in methods
        ]
        back_buttons = [
            build_back_button(data="back_to_select_method"),
            build_back_to_home_page_button()[0],
        ]
        keyboard = method_buttons + back_buttons
        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع لتعديلها:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    return SELECT_METHOD


back_to_select_method = start_update_payment_method


async def select_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data.startswith(
        "update_method_"
    ):
        method_id = int(update.callback_query.data.replace("update_method_", ""))
        context.user_data["update_method_id"] = method_id
    else:
        method_id = context.user_data["update_method_id"]
    with models.session_scope() as s:
        method = s.query(models.PaymentMethod).get(method_id)
        context.user_data["method_obj"] = method
        msg = method.stringify()

    changes = (
        "\n\n"
        "التغييرات:\n"
        f"الاسم: {context.user_data.get('edit_name', '')}\n"
        f"التفاصيل: {context.user_data.get('edit_details', '')}\n"
        f"النوع: {context.user_data.get('edit_type', '')}\n"
        f"النمط: {context.user_data.get('edit_mode', '')}\n"
        f"الدولة: {context.user_data.get('edit_country', '')}"
    )
    keyboard = [
        *build_edit_fields_keyboard(),
        build_back_button(data="back_to_choose_field"),
        build_back_to_home_page_button()[0],
    ]
    if update.message:
        await update.message.reply_text(
            text=f"<b>تعديل وسيلة الدفع:</b>\n\n" + msg + changes,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await update.callback_query.edit_message_text(
            text=f"<b>تعديل وسيلة الدفع:</b>\n\n" + msg + changes,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    return CHOOSE_FIELD


back_to_choose_field = select_country


async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    back_buttons = [
        build_back_button(data="back_to_edit_field"),
        build_back_to_home_page_button()[0],
    ]
    await update.callback_query.edit_message_text(
        text="أرسل الاسم الجديد:",
        reply_markup=InlineKeyboardMarkup(back_buttons),
    )
    return EDIT_NAME


async def save_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["edit_name"] = update.message.text
    await select_method(update, context)
    return CHOOSE_FIELD


async def edit_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    back_buttons = [
        build_back_button(data="back_to_edit_field"),
        build_back_to_home_page_button()[0],
    ]
    await update.callback_query.edit_message_text(
        text="أرسل التفاصيل الجديدة:",
        reply_markup=InlineKeyboardMarkup(back_buttons),
    )
    return EDIT_DETAILS


async def save_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["edit_details"] = update.message.text
    await select_method(update, context)
    return CHOOSE_FIELD


async def edit_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        *build_payemnt_method_types_keyboard(),
        build_back_button(data="back_to_edit_field"),
        build_back_to_home_page_button()[0],
    ]
    await update.callback_query.edit_message_text(
        text="اختر النوع الجديد:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return EDIT_TYPE


async def save_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.callback_query.data.replace("_payment_method", "")
    context.user_data["edit_type"] = t
    await select_method(update, context)
    return CHOOSE_FIELD


async def edit_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        *build_payment_method_modes_keyboard(),
        build_back_button(data="back_to_edit_field"),
        build_back_to_home_page_button()[0],
    ]
    await update.callback_query.edit_message_text(
        text="اختر النمط الجديد:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return EDIT_MODE


async def save_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = update.callback_query.data.replace("_payment_method", "")
    context.user_data["edit_mode"] = m
    await select_method(update, context)
    return CHOOSE_FIELD


async def edit_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        *build_country_selection_keyboard(),
        build_back_button(data="back_to_edit_field"),
        build_back_to_home_page_button()[0],
    ]
    await update.callback_query.edit_message_text(
        text="اختر الدولة الجديدة:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return EDIT_COUNTRY


back_to_edit_field = select_method


async def save_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = update.callback_query.data.replace("country_", "")
    context.user_data["edit_country"] = c
    await select_method(update, context)
    return CHOOSE_FIELD


async def confirm_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    method_id = context.user_data["update_method_id"]
    with models.session_scope() as s:
        method = s.query(models.PaymentMethod).get(method_id)
        if "edit_name" in context.user_data:
            method.name = context.user_data["edit_name"]
            context.user_data.pop("edit_name")
        if "edit_details" in context.user_data:
            method.details = context.user_data["edit_details"]
            context.user_data.pop("edit_details")
        if "edit_type" in context.user_data:
            method.type = context.user_data["edit_type"]
            context.user_data.pop("edit_type")
        if "edit_mode" in context.user_data:
            method.mode = context.user_data["edit_mode"]
            context.user_data.pop("edit_mode")
        if "edit_country" in context.user_data:
            method.country = context.user_data["edit_country"]
            context.user_data.pop("edit_country")
        s.commit()
        msg = method.stringify()
    await update.callback_query.edit_message_text(
        text=(
            f"تم تحديث وسيلة الدفع بنجاح:\n\n" + msg + "\n\n" + "اضغط /admin للمتابعة"
        )
    )
    return ConversationHandler.END


update_payment_method_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            start_update_payment_method,
            pattern=r"^update_payemnt_method$",
        )
    ],
    states={
        SELECT_COUNTRY: [
            CallbackQueryHandler(
                select_country,
                pattern=r"^country_(uae|syria)$",
            )
        ],
        SELECT_METHOD: [
            CallbackQueryHandler(
                select_method,
                pattern=r"^update_method_\d+$",
            )
        ],
        CHOOSE_FIELD: [
            CallbackQueryHandler(
                edit_name,
                pattern=r"^edit_name$",
            ),
            CallbackQueryHandler(
                edit_details,
                pattern=r"^edit_details$",
            ),
            CallbackQueryHandler(
                edit_type,
                pattern=r"^edit_type$",
            ),
            CallbackQueryHandler(
                edit_mode,
                pattern=r"^edit_mode$",
            ),
            CallbackQueryHandler(
                edit_country,
                pattern=r"^edit_country$",
            ),
            CallbackQueryHandler(
                confirm_update,
                pattern=r"^confirm_update$",
            ),
        ],
        EDIT_NAME: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                save_name,
            )
        ],
        EDIT_DETAILS: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                save_details,
            )
        ],
        EDIT_TYPE: [
            CallbackQueryHandler(
                save_type,
                pattern=r"^(deposit|withdraw|both)_payment_method$",
            )
        ],
        EDIT_MODE: [
            CallbackQueryHandler(
                save_mode,
                pattern=r"^(manual|auto|stripe)_payment_method$",
            )
        ],
        EDIT_COUNTRY: [
            CallbackQueryHandler(
                save_country,
                pattern=r"^country_(uae|syria)$",
            )
        ],
    },
    fallbacks=[
        admin_command,
        back_to_admin_home_page_handler,
        payment_method_settings_handler,
        CallbackQueryHandler(back_to_edit_field, pattern=r"^back_to_edit_field$"),
        CallbackQueryHandler(back_to_select_method, pattern=r"^back_to_select_method$"),
        CallbackQueryHandler(back_to_choose_field, pattern=r"^back_to_choose_field$"),
    ],
)


SHOW_COUNTRY = range(1)


async def show_payment_methods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = [
            *build_country_selection_keyboard(),
            build_back_button(data="back_to_payment_method_settings"),
            build_back_to_home_page_button()[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر الدولة لعرض وسائل الدفع",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return SHOW_COUNTRY


async def show_methods_for_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        country = update.callback_query.data.replace("country_", "")
        with models.session_scope() as s:
            methods = s.query(models.PaymentMethod).filter_by(country=country).all()
            if not methods:
                await update.callback_query.answer(
                    text=f"لا توجد وسائل دفع مضافة لهذه الدولة ({country})",
                    show_alert=True,
                )
                return
            msg = "\n\n".join(m.stringify() for m in methods)
            await update.callback_query.edit_message_text(
                text=(
                    f"وسائل الدفع ({country}):\n\n"
                    + msg
                    + "\n\n"
                    + "اضغط /admin للمتابعة"
                )
            )
        return ConversationHandler.END


show_payment_methods_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            show_payment_methods,
            r"^show_payemnt_methods$",
        )
    ],
    states={
        SHOW_COUNTRY: [
            CallbackQueryHandler(
                show_methods_for_country,
                r"^country_(uae|syria)$",
            )
        ],
    },
    fallbacks=[
        admin_command,
        back_to_admin_home_page_handler,
        payment_method_settings_handler,
    ],
)
