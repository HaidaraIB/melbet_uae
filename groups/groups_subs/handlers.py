from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from groups.groups_subs.functions import (
    renew_sub,
    make_group_sub_button_text,
    make_group_details_text,
    get_or_create_group_sub,
    schedule_expiring_jobs,
)
from groups.groups_subs.lang_dicts import *
from groups.group_preferences.functions import check_admin
from common.common import get_lang
import models


async def activate_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    if update.effective_chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        await update.message.reply_text(text=TEXTS[lang]["use_in_groups"])
        return

    group_id = update.effective_chat.id

    is_admin = await check_admin(
        context=context, group_id=group_id, user_id=user_id, lang=lang
    )
    if not is_admin:
        return

    with models.session_scope() as session:
        sub = get_or_create_group_sub(
            session=session, group_id=group_id, admin_id=user_id
        )
        expiring_notification = context.job_queue.get_jobs_by_name(
            f"notify_expiring_subs_{group_id}"
        )
        if not expiring_notification:
            schedule_expiring_jobs(context=context, sub=sub)
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=TEXTS[lang]["group_activate_success"].format(group_id),
                )
            except Exception:
                pass
    await update.message.reply_text(text=TEXTS[lang]["done"])


async def groups_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        user_id = update.effective_user.id
        lang = get_lang(user_id)
        with models.session_scope() as session:
            subs = (
                session.query(models.GroupSubscription)
                .filter_by(admin_id=user_id)
                .all()
            )
            if not subs:
                await update.message.reply_text(text=TEXTS[lang]["no_groups_yet"])
                return

            keyboard = [
                [
                    InlineKeyboardButton(
                        text=make_group_sub_button_text(lang=lang, sub=sub),
                        callback_data=f"show_group_sub_{sub.group_id}",
                    )
                ]
                for sub in subs
            ]
        await update.message.reply_text(
            text=TEXTS[lang]["choose_sub"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def show_group_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        user_id = update.effective_user.id
        lang = get_lang(user_id)
        group_id = int(update.callback_query.data.split("_")[-1])
        keyboard = [
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["activate_sub"],
                    callback_data=f"activate_group_sub_{group_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["deactivate_sub"],
                    callback_data=f"deactivate_group_sub_{group_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["renew_sub"],
                    callback_data=f"renew_group_sub_{group_id}",
                )
            ],
        ]
        with models.session_scope() as session:
            sub = (
                session.query(models.GroupSubscription)
                .filter_by(group_id=group_id)
                .first()
            )
            if not sub:
                await update.callback_query.answer(
                    text=TEXTS[lang]["group_not_found"],
                    show_alert=True,
                )
                return

            await update.callback_query.edit_message_text(
                text=make_group_details_text(lang=lang, group_id=group_id, sub=sub),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )


async def activate_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        user_id = update.effective_user.id
        lang = get_lang(user_id)
        group_id = int(update.callback_query.data.split("_")[-1])
        with models.session_scope() as session:
            sub = (
                session.query(models.GroupSubscription)
                .filter_by(group_id=group_id)
                .first()
            )
            if sub:
                sub.is_active = True
                session.commit()
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["activate_sub_success"]
        )


async def deactivate_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        user_id = update.effective_user.id
        lang = get_lang(user_id)
        group_id = int(update.callback_query.data.split("_")[-1])
        with models.session_scope() as session:
            sub = (
                session.query(models.GroupSubscription)
                .filter_by(group_id=group_id)
                .first()
            )
            if sub:
                sub.is_active = False
                session.commit()
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["deactivate_sub_success"]
        )


async def renew_group_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        user_id = update.effective_user.id
        lang = get_lang(user_id)
        query = update.callback_query
        group_id = int(query.data.split("_")[-1])
        payment_link = f"https://your-payment-gateway.com/pay?group_id={group_id}"
        await query.edit_message_text(
            text=TEXTS[lang]["pay_msg"].format(group_id, payment_link),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text=BUTTONS[lang]["confirm_payment"],
                    callback_data=f"confirm_group_sub_payment_{group_id}",
                )
            ),
        )


async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        user_id = update.effective_user.id
        lang = get_lang(user_id)
        query = update.callback_query
        group_id = int(query.data.split("_")[-1])
        with models.session_scope() as session:
            sub = renew_sub(session, group_id, months=1)
            expiring_notification = context.job_queue.get_jobs_by_name(
                f"notify_expiring_subs_{group_id}"
            )
            if expiring_notification:
                for job in expiring_notification:
                    job.schedule_removal()
            schedule_expiring_jobs(context=context, sub=sub)
        await query.edit_message_text(text=TEXTS[lang]["group_sub_payment_confirmed"])


groups_settings_handler = CommandHandler(
    "groups_settings",
    groups_settings,
)
activate_group_handler = CommandHandler(
    "activate",
    activate_group,
)

show_group_details_handler = CallbackQueryHandler(
    show_group_details,
    pattern=r"^show_group_sub_",
)
activate_sub_handler = CallbackQueryHandler(
    activate_sub,
    pattern=r"^activate_group_sub_",
)
deactivate_sub_handler = CallbackQueryHandler(
    deactivate_sub,
    pattern=r"^deactivate_group_sub_",
)
renew_group_sub_handler = CallbackQueryHandler(
    renew_group_sub,
    pattern=r"^renew_group_sub_",
)
confirm_group_payment_handler = CallbackQueryHandler(
    confirm_payment,
    pattern=r"^confirm_group_sub_payment_",
)
