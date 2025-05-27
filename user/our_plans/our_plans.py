from telegram import Chat, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from common.lang_dicts import *
from common.common import get_lang
from common.keyboards import build_back_button, build_back_to_home_page_button
from common.back_to_home_page import back_to_user_home_page_handler
from user.our_plans.common import build_plans_keyboard, PLANS
import models
from start import start_command

PLAN, MULTIPLIER, DAYS, PAY = range(4)


async def our_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        keyboard = build_plans_keyboard(lang=lang)
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=False)[0])
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["choose_plan"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return PLAN


async def choose_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button(data="back_to_choose_plan", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        if not update.callback_query.data.startswith("back"):
            plan_code = update.callback_query.data
            context.user_data["plan_code"] = plan_code
        else:
            plan_code = context.user_data["plan_code"]
        if plan_code == "capital_management":
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["get_capital_management_plan"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return MULTIPLIER
        else:
            keyboard = [
                [
                    InlineKeyboardButton(
                        text=f"{BUTTONS[lang]["pay"]} {PLANS[lang][plan_code]['price']}",
                        callback_data=f"pay_plan_{plan_code}",
                    )
                ],
                *back_buttons,
            ]
            await update.callback_query.edit_message_text(
                text=PLANS[lang][plan_code]["details"],
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return PAY


back_to_choose_plan = our_plans


async def get_multiplier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button(data="back_to_get_multiplier", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        if update.message:
            multiplier = float(update.message.text)
            if multiplier < 2 or multiplier > 20:
                await update.message.reply_text(
                    text=TEXTS[lang]["get_capital_management_plan"],
                )
                return
            context.user_data["multiplier"] = multiplier
            await update.message.reply_text(
                text=TEXTS[lang]["get_capital_management_days"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["get_capital_management_days"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return DAYS


back_to_get_multiplier = choose_plan


async def get_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        days = int(update.message.text)
        if days < 3 or days > 60:
            await update.message.reply_text(
                text=TEXTS[lang]["get_capital_management_days"]
            )
            return
        multiplier = context.user_data.get("multiplier", 2)
        price = int(max((multiplier * 30) / days * 1.5, 30))
        context.user_data["price"] = price
        keyboard = [
            [
                InlineKeyboardButton(
                    text=f"{BUTTONS[lang]["pay"]} {price}$",
                    callback_data=f"pay_capital_{multiplier}_{days}",
                )
            ],
            build_back_button("back_to_get_days"),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        await update.message.reply_text(
            text=TEXTS[lang]["capital_management_order_summary"].format(
                multiplier, days, price
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return PAY

back_to_get_days = get_multiplier

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        await update.callback_query.answer(
            text=update.callback_query.data,
            show_alert=True,
        )


our_plans_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            our_plans,
            "^our_plans$",
        ),
    ],
    states={
        PLAN: [
            CallbackQueryHandler(
                choose_plan, lambda x: x in PLANS[models.Language.ARABIC]
            )
        ],
        MULTIPLIER: [
            MessageHandler(
                filters=filters.Regex("^[0-9]+$"),
                callback=get_multiplier,
            ),
        ],
        DAYS: [
            MessageHandler(
                filters=filters.Regex("^[0-9]+$"),
                callback=get_days,
            ),
        ],
        PAY: [
            CallbackQueryHandler(
                pay,
                "^pay_((capital)|(plan))",
            )
        ],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(back_to_choose_plan, "^back_to_choose_plan$"),
        CallbackQueryHandler(back_to_get_multiplier, "^back_to_get_multiplier$"),
        CallbackQueryHandler(back_to_get_days, "^back_to_get_days$"),
    ],
)
