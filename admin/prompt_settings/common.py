from telegram import InlineKeyboardButton


def prompt_panel():
    return [
        [
            InlineKeyboardButton(
                "برومبت المراقبة 🛂",
                callback_data="edit_prompt_monitor",
            ),
            InlineKeyboardButton(
                "برومبت رسائل الأمان 🛡",
                callback_data="edit_prompt_security_messages",
            ),
        ],
        [
            InlineKeyboardButton(
                "برومبت الإيداع 📥",
                callback_data="edit_prompt_deposit",
            ),
            InlineKeyboardButton(
                "برومبت السحب 📤",
                callback_data="edit_prompt_withdraw",
            ),
        ],
        [
            InlineKeyboardButton(
                "برومبت المدير 👤",
                callback_data="edit_prompt_manager",
            )
        ],
        [
            InlineKeyboardButton(
                "برومبت الترويج 🎟",
                callback_data="edit_prompt_promotional",
            ),
            InlineKeyboardButton(
                "برومبت ملخص المباريات ⚽️",
                callback_data="edit_prompt_match_summary",
            ),
        ],
        [
            InlineKeyboardButton(
                "برومبت تغيير الحساب ✏️",
                callback_data="edit_prompt_change_account",
            )
        ],
    ]
