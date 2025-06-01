from groups.groups_subs.lang_dicts import *
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from common.common import get_lang
from telegram.ext import ContextTypes
import models
import logging

log = logging.getLogger(__name__)


async def notify_expiring_subs(context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context.job.user_id)
    group_id = context.job.chat_id
    with models.session_scope() as session:
        sub = (
            session.query(models.GroupSubscription).filter_by(group_id=group_id).first()
        )
        if sub:
            try:
                await context.bot.send_message(
                    chat_id=sub.admin_id,
                    text=TEXTS[lang]["sub_expire_notification"].format(sub.group_id),
                    reply_markup=InlineKeyboardMarkup.from_button(
                        InlineKeyboardButton(
                            text=BUTTONS[lang]["renew_sub"],
                            callback_data=f"renew_group_sub_{sub.group_id}",
                        )
                    ),
                )
            except Exception as e:
                log.error(f"Failed to notify admin {sub.admin_id}: {e}")


async def expire_sub(context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context.job.user_id)
    group_id = context.job.chat_id
    with models.session_scope() as session:
        sub = (
            session.query(models.GroupSubscription).filter_by(group_id=group_id).first()
        )
        if sub:
            sub.status = "expired"
            sub.is_active = False
            session.commit()
            try:
                await context.bot.send_message(
                    chat_id=sub.admin_id,
                    text=TEXTS[lang]["sub_expired"].format(sub.group_id),
                    reply_markup=InlineKeyboardMarkup.from_button(
                        InlineKeyboardButton(
                            text=BUTTONS[lang]["renew_sub"],
                            callback_data=f"renew_group_sub_{sub.group_id}",
                        )
                    ),
                )
            except Exception as e:
                log.error(
                    f"Failed to notify admin about sub expire {sub.admin_id}: {e}"
                )
