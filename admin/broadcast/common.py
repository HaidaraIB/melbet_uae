from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes
from common.keyboards import build_back_button, build_back_to_home_page_button
import models


def build_broadcast_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="الجميع 👥",
                callback_data="everyone",
            ),
            InlineKeyboardButton(
                text="مستخدمين محددين 👤",
                callback_data="specific_users",
            ),
        ],
        [
            InlineKeyboardButton(
                text="جميع المستخدمين 👨🏻‍💼",
                callback_data="all_users",
            ),
            InlineKeyboardButton(
                text="جميع الآدمنز 🤵🏻",
                callback_data="all_admins",
            ),
        ],
        [
            InlineKeyboardButton(
                text="قناة أو مجموعة 📢",
                callback_data="channel_or_group",
            ),
        ],
        build_back_button("back_to_the_message"),
        build_back_to_home_page_button()[0],
    ]
    return InlineKeyboardMarkup(keyboard)


async def send_to(users: list[int], context: ContextTypes.DEFAULT_TYPE):
    msg: Message = context.user_data["the_message"]
    media_types = {
        "photo": msg.photo[-1] if msg.photo else None,
        "video": msg.video,
        "audio": msg.audio,
        "voice": msg.voice,
    }
    media = None
    media_type = None
    for m_type, m in media_types.items():
        if m:
            media = m
            media_type = m_type
            break

    for user in users:
        try:
            if media:
                send_func = getattr(context.bot, f"send_{media_type}")
                await send_func(
                    chat_id=user,
                    caption=msg.caption,
                    **{media_type: media},
                )
            else:
                await context.bot.send_message(chat_id=user, text=msg.text)
        except:
            continue
