import models
from datetime import datetime, timedelta
from common.constants import TIMEZONE
from sqlalchemy.orm import Session

TRIAL_DAYS = 3


def get_or_create_group_sub(session: Session, group_id: int, admin_id: int = None):
    sub = session.query(models.GroupSubscription).filter_by(group_id=group_id).first()
    if not sub:
        sub = models.GroupSubscription(
            group_id=group_id,
            is_active=True,
            trial_used=True,
            expire_date=datetime.now(TIMEZONE) + timedelta(days=TRIAL_DAYS),
            admin_id=admin_id,
        )
        session.add(sub)
        session.commit()
    return sub


def check_group_sub(session: Session, group_id: int):
    sub = get_or_create_group_sub(session, group_id)
    if sub.is_active and (
        not sub.expire_date
        or sub.expire_date.astimezone(TIMEZONE) > datetime.now(TIMEZONE)
    ):
        return True
    return False


def renew_sub(
    session: Session,
    group_id: int,
    plan_code: str = "default",
    months: int = 1,
):
    sub = get_or_create_group_sub(session, group_id)
    new_exp = datetime.now(TIMEZONE) + timedelta(days=30 * months)
    sub.expire_date = new_exp
    sub.is_active = True
    sub.plan_code = plan_code
    session.commit()


def make_group_sub_button_text(lang: models.Language, group_id: int, session: Session):
    if lang == models.Language.ARABIC:
        return f"غروب {group_id} - {'فعال' if check_group_sub(session, group_id) else 'منتهي'}"
    elif lang == models.Language.ENGLISH:
        return f"Group {group_id} - {'active' if check_group_sub(session, group_id) else 'expired'}"


def make_group_details_text(
    lang: models.Language,
    group_id: int,
    sub: models.GroupSubscription,
):
    if lang == models.Language.ARABIC:
        return (
            f"غروب: {group_id}\n"
            f"الحالة: {'✅ فعال' if sub.is_active else '❌ منتهي'}\n"
            f"ينتهي في: {sub.expire_date.strftime('%Y-%m-%d %H:%M') if sub.expire_date else 'غير محدد'}\n"
        )
    elif lang == models.Language.ENGLISH:
        return (
            f"Group: {group_id}\n"
            f"Status: {'✅ active' if sub.is_active else '❌ expired'}\n"
            f"Ends at: {sub.expire_date.strftime('%Y-%m-%d %H:%M') if sub.expire_date else 'Undefined'}\n"
        )
