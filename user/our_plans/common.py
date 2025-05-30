from telegram import InlineKeyboardButton
from telegram.ext import ContextTypes
import models
from common.lang_dicts import *


def build_plans_keyboard(lang: models.Language):
    with models.session_scope() as s:
        plans = s.query(models.Plan).all()
        return [
            [
                InlineKeyboardButton(
                    text=p.name_ar if lang == models.Language.ARABIC else p.name_en,
                    callback_data=p.code,
                )
            ]
            for p in plans
        ]


def calc_capital_management_price(multiplier: float, days: int):
    return int(max((multiplier * 30) / days * 1.5, 30))


async def job_expire_subscription(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    user_id = context.job.user_id
    subscription_id = job_data["subscription_id"]

    with models.session_scope() as s:
        user = s.get(models.User, user_id)
        subscription = (
            s.query(models.Subscription).filter_by(id=subscription_id).first()
        )
        if not subscription:
            return

        # تعديل حالة الاشتراك
        subscription.status = "expired"
        user.plan_code = None
        s.commit()

        await context.bot.send_message(
            chat_id=user.user_id,
            text=TEXTS[user.lang]["subscription_expired"],
        )
