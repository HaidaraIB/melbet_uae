from telegram import InlineKeyboardButton


def build_payemnt_methods_settings_keyboard():
    return [
        [
            InlineKeyboardButton(
                text="إضافة ➕",
                callback_data="add_payemnt_method",
            ),
            # InlineKeyboardButton(
            #     text="تعديل 🔄",
            #     callback_data="update_payemnt_method",
            # ),
        ]
    ]


def build_payemnt_method_types_keyboard():
    return [
        [
            InlineKeyboardButton(
                text="إيداع",
                callback_data="deposit_payment_method",
            ),
            InlineKeyboardButton(
                text="سحب",
                callback_data="withdraw_payemnt_method",
            ),
        ],
        [
            InlineKeyboardButton(
                text="إيداع وسحب",
                callback_data="both_payment_method",
            ),
        ],
    ]


def build_payment_method_modes_keyboard():
    return [
        [
            InlineKeyboardButton(
                text="يدوي",
                callback_data="manual_payment_method",
            ),
            InlineKeyboardButton(
                text="آلي",
                callback_data="auto_payment_method",
            ),
        ]
        [
            InlineKeyboardButton(
                text="stripe",
                callback_data="stripe_payment_method",
            ),
        ]
    ]
