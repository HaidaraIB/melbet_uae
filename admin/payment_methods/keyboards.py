from telegram import InlineKeyboardButton


def build_country_selection_keyboard():
    return [
        [
            InlineKeyboardButton(
                text="🇦🇪 الإمارات",
                callback_data="country_uae",
            ),
            InlineKeyboardButton(
                text="🇸🇾 سوريا",
                callback_data="country_syria",
            ),
        ]
    ]


def build_payemnt_methods_settings_keyboard():
    return [
        [
            InlineKeyboardButton(
                text="إضافة ➕",
                callback_data="add_payemnt_method",
            ),
        ],
        [
            InlineKeyboardButton(
                text="عرض 👁️",
                callback_data="show_payemnt_methods",
            ),
        ],
        [
            InlineKeyboardButton(
                text="تعديل 🔄",
                callback_data="update_payemnt_method",
            ),
        ],
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
        ],
        [
            InlineKeyboardButton(
                text="stripe",
                callback_data="stripe_payment_method",
            ),
        ],
    ]


def build_edit_fields_keyboard(is_active: bool):
    return [
        [
            InlineKeyboardButton(
                "إلغاء تفعيل" if is_active else "تفعيل",
                callback_data=f"edit_status_{is_active}",
            )
        ],
        [
            InlineKeyboardButton(
                "الاسم",
                callback_data="edit_name",
            ),
            InlineKeyboardButton(
                "التفاصيل",
                callback_data="edit_details",
            ),
        ],
        [
            InlineKeyboardButton(
                "النوع",
                callback_data="edit_type",
            ),
            InlineKeyboardButton(
                "النمط",
                callback_data="edit_mode",
            ),
        ],
        [
            InlineKeyboardButton(
                "الدولة",
                callback_data="edit_country",
            )
        ],
        [
            InlineKeyboardButton(
                "حفظ التعديلات ✅",
                callback_data="confirm_update",
            )
        ],
        [
            InlineKeyboardButton(
                "حذف الوسيلة ❌",
                callback_data="delete_method",
            )
        ],
    ]
