from telegram import InlineKeyboardButton


def prompt_panel():
    return [
        [
            InlineKeyboardButton(
                "برومبت المراقبة 🛡",
                callback_data="edit_prompt_monitor",
            )
        ],
        [
            InlineKeyboardButton(
                "برومبت الجلسات 🤖",
                callback_data="edit_prompt_session",
            )
        ],
        [
            InlineKeyboardButton(
                "برومبت المدير 👤",
                callback_data="edit_prompt_manager",
            )
        ],
        [
            InlineKeyboardButton(
                "برومبت تغيير الحساب ✏️",
                callback_data="edit_prompt_change_account",
            )
        ],
    ]
