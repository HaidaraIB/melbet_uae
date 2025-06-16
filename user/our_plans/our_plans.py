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
from common.keyboards import (
    build_back_button,
    build_back_to_home_page_button,
    build_user_keyboard,
)
from common.constants import TIMEZONE
from common.back_to_home_page import back_to_user_home_page_handler
from user.our_plans.common import (
    build_plans_keyboard,
    calc_capital_management_price,
    job_expire_subscription,
)
import models
from start import start_command
from datetime import datetime, timedelta

PLAN, MULTIPLIER, DAYS, PAY, PAYMENT_DONE = range(5)


async def our_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)

        await update.callback_query.answer(text=TEXTS[lang]["soon"], show_alert=True)
        return ConversationHandler.END

        with models.session_scope() as s:
            user = s.get(models.User, update.effective_user.id)
            if user.plan_code:
                await update.callback_query.answer(
                    text=TEXTS[lang]["already_subscribed"],
                    show_alert=True,
                )
                return
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
            with models.session_scope() as s:
                plan = s.query(models.Plan).filter_by(code=plan_code).first()
                keyboard = [
                    [
                        InlineKeyboardButton(
                            text=f"{BUTTONS[lang]["pay"]} {plan.price}",
                            callback_data=f"pay_plan_{plan_code}",
                        )
                    ],
                    *back_buttons,
                ]
                await update.callback_query.edit_message_text(
                    text=(
                        plan.details_ar
                        if lang == models.Language.ARABIC
                        else plan.details_en
                    ),
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
        if update.message:
            days = int(update.message.text)
            if days < 3 or days > 60:
                await update.message.reply_text(
                    text=TEXTS[lang]["get_capital_management_days"]
                )
                return
            context.user_data["days"] = days
            multiplier = context.user_data["multiplier"]
            price = calc_capital_management_price(multiplier=multiplier, days=days)
            context.user_data["price"] = price
        else:
            price = context.user_data["price"]
            days = context.user_data["days"]
            multiplier = context.user_data["multiplier"]
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
        if update.message:
            await update.message.reply_text(
                text=TEXTS[lang]["capital_management_order_summary"].format(
                    multiplier, days, price
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
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
        query_data = update.callback_query.data

        if query_data.startswith("pay_plan_"):
            plan_code = query_data.replace("pay_plan_", "")
            with models.session_scope() as s:
                plan = s.query(models.Plan).filter_by(code=plan_code).first()
                price = plan.price
                plan_name = (
                    plan.name_ar if lang == models.Language.ARABIC else plan.name_en
                )
                details = (
                    plan.details_ar
                    if lang == models.Language.ARABIC
                    else plan.details_en
                )
                # (يمكنك هنا إنشاء فاتورة عبر API دفع وإضافة الرابط بالأسفل)
                payment_msg = TEXTS[lang]["pay_plan_msg"].format(
                    plan_name,
                    details,
                    price,
                    plan.max_odds,
                    plan.duration,
                    plan.vouchers,
                    price,
                )
                payment_done_button = InlineKeyboardButton(
                    text=BUTTONS[lang]["payment_done"],
                    callback_data=f"payment_done_plan_{plan_code}",
                )
        elif query_data.startswith("pay_capital_"):
            parts = query_data.split("_")
            multiplier = parts[2]
            days = parts[3]
            price = context.user_data.get("price", "غير معروف")
            payment_msg = TEXTS[lang]["pay_capital_msg"].format(
                multiplier, days, price, price
            )
            payment_done_button = InlineKeyboardButton(
                text=BUTTONS[lang]["payment_done"],
                callback_data=f"payment_done_capital_{multiplier}_{days}",
            )
        keyboard = [
            [payment_done_button],
            build_back_button(data="back_to_pay", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]
        await update.callback_query.edit_message_text(
            text=payment_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return PAYMENT_DONE


async def back_to_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan_code = context.user_data["plan_code"]
    if plan_code == "capital_management":
        return await get_days(update=update, context=context)
    else:
        return await choose_plan(update=update, context=context)


async def payment_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        user_id = update.effective_user.id
        query_data = update.callback_query.data
        if query_data.startswith("payment_done_plan_"):
            plan_code = query_data.replace("payment_done_plan_", "")
            multiplier = None
            days = None
            with models.session_scope() as s:
                plan = s.query(models.Plan).filter_by(code=plan_code).first()
                price = plan.price
        elif query_data.startswith("payment_done_capital_"):
            parts = query_data.replace("payment_done_capital_", "").split("_")
            plan_code = "capital_management"
            multiplier = parts[0]
            days = parts[1]
            price = calc_capital_management_price(
                multiplier=float(multiplier), days=int(days)
            )

        payment_success = True

        if payment_success:
            with models.session_scope() as s:
                user = s.query(models.User).filter_by(user_id=user_id).first()
                user.plan_code = plan_code
                s.commit()
                subscription = models.Subscription(
                    user_id=user.user_id,
                    plan_code=plan_code,
                    multiplier=multiplier,
                    days=days,
                    price=price,
                    remaining_vouchers=user.plan.vouchers,
                    status="active",
                )
                s.add(subscription)
                s.commit()
                context.job_queue.run_once(
                    callback=job_expire_subscription,
                    when=datetime.now(TIMEZONE) + timedelta(days=30),
                    # when=10,
                    data={
                        "subscription_id": subscription.id,
                    },
                    user_id=update.effective_user.id,
                    job_kwargs={
                        "id": f"job_expire_subscription_{subscription.id}",
                        "replace_existing": True,
                    },
                )
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["payment_success"],
                reply_markup=build_user_keyboard(lang=lang),
            )
            return ConversationHandler.END

        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["payment_failed"]
            )


def plans_pattern(data: str):
    with models.session_scope() as s:
        plans = s.query(models.Plan).all()
        return data in [p.code for p in plans]


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
                choose_plan,
                plans_pattern,
            )
        ],
        MULTIPLIER: [
            MessageHandler(
                filters=filters.Regex(r"^[0-9]+$"),
                callback=get_multiplier,
            ),
        ],
        DAYS: [
            MessageHandler(
                filters=filters.Regex(r"^[0-9]+$"),
                callback=get_days,
            ),
        ],
        PAY: [
            CallbackQueryHandler(
                pay,
                r"^pay_((capital)|(plan))",
            )
        ],
        PAYMENT_DONE: [
            CallbackQueryHandler(
                payment_done,
                r"^payment_done_",
            )
        ],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(back_to_choose_plan, r"^back_to_choose_plan$"),
        CallbackQueryHandler(back_to_get_multiplier, r"^back_to_get_multiplier$"),
        CallbackQueryHandler(back_to_get_days, r"^back_to_get_days$"),
        CallbackQueryHandler(back_to_pay, r"^back_to_pay$"),
    ],
    name="our_plans_conv",
    persistent=True,
)
