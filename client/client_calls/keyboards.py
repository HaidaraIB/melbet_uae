from telegram import InlineKeyboardButton
from telethon import Button


def build_process_deposit_options_keyboard(transaction_id: int):
    return [
        InlineKeyboardButton(
            text="تأكيد ✅",
            callback_data=f"confirm_approve_deposit_{transaction_id}",
        ),
        InlineKeyboardButton(
            text="تعديل المبلغ ✏️",
            callback_data=f"edit_amount_deposit_{transaction_id}",
        ),
    ]


def build_process_transaction_keyboard(
    transaction_type: str, transaction_id: int, lib: str
):
    if lib == "ptb":
        return [
            [
                InlineKeyboardButton(
                    text="موافقة ✅",
                    callback_data=f"approve_{transaction_type}_{transaction_id}",
                ),
                InlineKeyboardButton(
                    text="رفض ❌",
                    callback_data=f"decline_{transaction_type}_{transaction_id}",
                ),
            ]
        ]
    elif lib == "telethon":
        return [
            [
                Button.inline(
                    text="موافقة ✅",
                    data=f"approve_{transaction_type}_{transaction_id}",
                ),
                Button.inline(
                    text="رفض ❌",
                    data=f"decline_{transaction_type}_{transaction_id}",
                ),
            ]
        ]
