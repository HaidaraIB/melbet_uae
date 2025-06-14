from telegram import InlineKeyboardButton
import models
from common.lang_dicts import *


def build_preferences_keyboard(lang: str):
    return [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["choose_pref_for_me"],
                callback_data="choose_pref_for_me",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["choose_pref_sport"],
                callback_data="choose_pref_sport",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["choose_pref_matches"],
                callback_data="choose_pref_matches",
            )
        ],
    ]


def build_get_voucher_confirmation_keyboard(
    user_id: int,
    lang: models.Language,
    odds: int,
):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["confirm_payment"],
                callback_data="confirm_payment",
            ),
            InlineKeyboardButton(
                text=BUTTONS[lang]["cancel_voucher"],
                callback_data="cancel_voucher",
            ),
        ],
    ]
    with models.session_scope() as s:
        user = s.query(models.User).filter_by(user_id=user_id).first()
        subscriptions = (
            s.query(models.Subscription)
            .filter_by(user_id=user_id)
            .order_by(models.Subscription.created_at.desc())
            .all()
        )
        current_sub = subscriptions[0]
        if user.plan_code and user.plan_code != "capital_management":
            if current_sub.status == "active":
                current_plan: models.Plan = current_sub.plan
                sub_id = None
                # first check if previous_sub can fullfill this voucher
                if len(subscriptions) > 1:
                    previous_sub = subscriptions[1]
                    previous_plan: models.Plan = previous_sub.plan
                    if (
                        (
                            previous_plan.code == "plus"
                            and previous_sub.remaining_vouchers
                            >= int(0.2 * previous_plan.vouchers)
                        )
                        or (
                            previous_plan.code == "pro"
                            and previous_sub.remaining_vouchers > 0
                        )
                    ) and odds <= previous_plan.max_odds:
                        sub_id = previous_sub.id
                    elif (
                        current_sub.remaining_vouchers > 0
                        and odds <= current_plan.max_odds
                    ):
                        sub_id = current_sub.id
                elif (
                    current_sub.remaining_vouchers > 0 and odds <= current_plan.max_odds
                ):
                    sub_id = current_sub.id
                if sub_id is not None:
                    keyboard.insert(
                        0,
                        [
                            InlineKeyboardButton(
                                text=BUTTONS[lang]["use_sub"],
                                callback_data=f"use_sub_{sub_id}",
                            )
                        ],
                    )

    return keyboard
