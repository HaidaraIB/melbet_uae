from telegram import InlineKeyboardButton
import models


def build_admin_settings_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="إضافة آدمن ➕",
                callback_data="add_admin",
            ),
            InlineKeyboardButton(
                text="حذف آدمن ✖️",
                callback_data="remove_admin",
            ),
        ],
        [
            InlineKeyboardButton(
                text="عرض الآدمنز الحاليين 👓",
                callback_data="show_admins",
            )
        ],
    ]
    return keyboard


def stringify_admin(admin: models.User):
    return (
        f"ID: <code>{admin.user_id}</code>\n"
        f"Username: {f'@{admin.username}' if admin.username else '<i>لا يوجد</i>'}\n"
        f"Full Name: {f'<b>{admin.name}</b>'}\n\n"
    )
