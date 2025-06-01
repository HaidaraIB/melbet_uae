from groups.groups_subs.lang_dicts import *
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from common.common import get_lang
from telegram.ext import ContextTypes
import models
from datetime import datetime, timedelta
from common.constants import TIMEZONE
import logging

log = logging.getLogger(__name__)


async def notify_expiring_subs(context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context.job.user_id)
    with models.session_scope() as session:
        soon = datetime.now(TIMEZONE) + timedelta(days=1)
        subs = (
            session.query(models.GroupSubscription)
            .filter(
                models.GroupSubscription.is_active == True,
                models.GroupSubscription.expire_date != None,
                models.GroupSubscription.expire_date <= soon,
                models.GroupSubscription.expire_date > datetime.now(TIMEZONE),
            )
            .all()
        )
        for sub in subs:
            if sub.admin_id:
                try:
                    await context.bot.send_message(
                        chat_id=sub.admin_id,
                        text=TEXTS[lang]["sub_expire_notification"],
                        reply_markup=InlineKeyboardMarkup.from_button(
                            InlineKeyboardButton(
                                text=BUTTONS[lang]["renew_sub"],
                                callback_data=f"pay_group_sub_{sub.group_id}",
                            )
                        ),
                    )
                except Exception as e:
                    log.error(f"Failed to notify admin {sub.admin_id}: {e}")
