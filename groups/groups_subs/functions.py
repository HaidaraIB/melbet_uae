from telegram.ext import ContextTypes
import models
from datetime import datetime, timedelta
from common.constants import TIMEZONE
from sqlalchemy.orm import Session
from groups.groups_subs.jobs import notify_expiring_subs, expire_sub
from groups.groups_subs.constants import *


def schedule_expiring_jobs(
    context: ContextTypes.DEFAULT_TYPE, sub: models.GroupSubscription
):
    context.job_queue.run_once(
        callback=notify_expiring_subs,
        when=sub.expire_date - timedelta(days=1),
        name=f"notify_expiring_subs_{sub.group_id}",
        user_id=sub.admin_id,
        chat_id=sub.group_id,
        job_kwargs={
            "id": f"notify_expiring_subs_{sub.group_id}",
            "misfire_grace_time": None,
        },
    )
    context.job_queue.run_once(
        callback=expire_sub,
        when=sub.expire_date,
        name=f"notify_expiring_subs_{sub.group_id}",
        user_id=sub.admin_id,
        chat_id=sub.group_id,
        job_kwargs={
            "id": f"expire_sub_{sub.group_id}",
            "misfire_grace_time": None,
        },
    )


def get_or_create_group_sub(session: Session, group_id: int, admin_id: int = None):
    sub = session.query(models.GroupSubscription).filter_by(group_id=group_id).first()
    if not sub:
        sub = models.GroupSubscription(
            group_id=group_id,
            is_active=True,
            expire_date=datetime.now(TIMEZONE) + timedelta(days=TRIAL_DAYS),
            admin_id=admin_id,
        )
        session.add(sub)
        user = session.query(models.User).filter_by(user_id=admin_id).first()
        user.trial_used = True
        session.commit()
    return sub


def check_group_sub(session: Session, group_id: int):
    sub = get_or_create_group_sub(session, group_id)
    expire_date: datetime = sub.expire_date
    if sub.is_active and (
        not expire_date or expire_date.replace(tzinfo=TIMEZONE) > datetime.now(TIMEZONE)
    ):
        return True
    return False


def renew_sub(
    session: Session,
    group_id: int,
    plan_code: str = "default",
    months: int = 1,
):
    sub = session.query(models.GroupSubscription).filter_by(group_id=group_id).first()
    new_exp = sub.expire_date + timedelta(days=30 * months)
    sub.expire_date = new_exp
    sub.is_active = True
    sub.plan_code = plan_code
    session.commit()
    return sub


def make_group_sub_button_text(lang: models.Language, sub: models.GroupSubscription):

    if lang == models.Language.ARABIC:
        return f"غروب {sub.group_id} - {EN_TO_AR_STATUS_DICT[sub.status]}"
    elif lang == models.Language.ENGLISH:
        return f"Group {sub.group_id} - {sub.status}"


def make_group_details_text(
    lang: models.Language,
    group_id: int,
    sub: models.GroupSubscription,
):
    if lang == models.Language.ARABIC:
        return (
            f"غروب: <code>{group_id}</code>\n"
            f"الحالة: {EN_TO_AR_STATUS_DICT[sub.status]}\n"
            f"ينتهي في:\n{sub.expire_date.strftime('%Y-%m-%d %H:%M') if sub.expire_date else 'غير محدد'}\n"
        )
    elif lang == models.Language.ENGLISH:
        return (
            f"Group: <code>{group_id}</code>\n"
            f"Status: {sub.status}\n"
            f"Ends at:\n{sub.expire_date.strftime('%Y-%m-%d %H:%M') if sub.expire_date else 'Undefined'}\n"
        )
