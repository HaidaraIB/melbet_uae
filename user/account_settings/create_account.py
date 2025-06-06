from TeleClientSingleton import TeleClientSingleton
from telethon.tl.patched import Message
from telethon import types, events
from common.lang_dicts import *
import models
import logging

log = logging.getLogger(__name__)

WELCOME_BONUS_888STARZ_BASE_URL = "https://buy785.online/L?tag=d_4440809m_37513c_{}&pb=b3b03bfe91044205ac457c6bf7b551a4&click_id={}"
APK_DOWNLOAD_888STARZ_BASE_URL = "https://buy785.online/L?tag=d_4440809m_63871c_{}&pb=b3b03bfe91044205ac457c6bf7b551a4&click_id={}"


async def create_account(event: events.newmessage.NewMessage.Event):
    msg: Message = event.message
    sender: types.User = msg.sender
    with models.session_scope() as s:
        user = s.get(models.User, msg.sender_id)
        if not user:
            user = models.User(
                user_id=msg.sender_id,
                username=sender.username or "N/A",
                name=(sender.first_name or "") + " " + (sender.last_name or ""),
            )
            s.add(user)
            s.commit()
        try:
            await TeleClientSingleton().send_message(
                entity=user.user_id,
                message=TEXTS[user.lang]["create_account_group_reply"].format(
                    user.name,
                    WELCOME_BONUS_888STARZ_BASE_URL.format(user.user_id, user.user_id),
                    APK_DOWNLOAD_888STARZ_BASE_URL.format(user.user_id, user.user_id),
                ),
                link_preview=False,
                parse_mode="html",
            )
        except Exception as e:
            await TeleClientSingleton().send_message(
                event.chat_id,
                message=TEXTS[user.lang]["start_chat_first"],
            )
            return
        await TeleClientSingleton().send_message(
            event.chat_id,
            message=TEXTS[user.lang]["link_sent_in_private"],
        )


# from telegram import Update, Chat
# from telegram.ext import ContextTypes
# from telegram.constants import ChatMemberStatus
# async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
#         sender = update.effective_sender
#         chat_member = await context.bot.get_chat_member(
#             chat_id=update.effective_chat.id, user_id=sender.id
#         )
#         if chat_member.status != ChatMemberStatus.MEMBER:
#             return
#         with models.session_scope() as s:
#             user = s.get(models.User, sender.id)
#             if not user:
#                 user = models.User(
#                     user_id=sender.id,
#                     username=sender.username or "N/A",
#                     name=sender.full_name,
#                 )
#                 s.add(user)
#                 s.commit()
#             text = update.effective_message.text
#             if "حساب" in text:
#                 referral_link = f"{STARZ888_BASE_URL}&subid={user.user_id}"
#                 try:
#                     await update.message.reply_text(
#                         text=TEXTS[user.lang]["create_account_group_reply"].format(
#                             user.name, user.username, referral_link
#                         )
#                     )
#                 except Exception as e:
#                     log.error(f"❌ Failed to send to {user.user_id}: {e}")
