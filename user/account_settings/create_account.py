from TeleClientSingleton import TeleClientSingleton
from TeleBotSingleton import TeleBotSingleton
from Config import Config
from telethon.tl.patched import Message
from telethon import types, events, Button
from common.lang_dicts import *
import models
import logging
from client.client_calls.functions import now_iso
from user.account_settings.functions import check_reg_account
from common.constants import *

log = logging.getLogger(__name__)


async def create_account(event: events.newmessage.NewMessage.Event):
    msg: Message = event.message
    if (
        await TeleClientSingleton().get_permissions(
            entity=event.chat_id, user=msg.sender_id
        )
    ).is_admin:
        return
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
            message = TEXTS[user.lang]["create_account_group_reply"].format(
                user.name,
                CREATE_ACCOUNT_LINKS[event.chat_id]["wlcm"].format(
                    user.user_id, user.user_id
                ),
                CREATE_ACCOUNT_LINKS[event.chat_id]["apk"].format(
                    user.user_id, user.user_id
                ),
                CREATE_ACCOUNT_LINKS[event.chat_id]["reg"].format(
                    user.user_id, user.user_id
                ),
            )
            if event.chat_id == Config.SYR_MONITOR_GROUP_ID and any(
                kw in msg.raw_text.lower() for kw in ["نقاط", "points", "point"]
            ):
                message = TEXTS[user.lang]["create_account_group_reply"].format(
                    user.name,
                    CREATE_ACCOUNT_LINKS[Config.UAE_MONITOR_GROUP_ID]["wlcm"].format(
                        -user.user_id, -user.user_id
                    ),
                    CREATE_ACCOUNT_LINKS[Config.UAE_MONITOR_GROUP_ID]["apk"].format(
                        -user.user_id, -user.user_id
                    ),
                    CREATE_ACCOUNT_LINKS[Config.UAE_MONITOR_GROUP_ID]["reg"].format(
                        -user.user_id, -user.user_id
                    ),
                )

            await TeleClientSingleton().send_message(
                entity=user.user_id,
                message=message,
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
    raise events.StopPropagation


async def handle_link_account_request(event: events.CallbackQuery.Event):
    data: str = event.data.decode("utf-8")
    event.data_match
    user_id = int(data.split("_")[-1])
    account_number = data.split("_")[-2]
    msg: Message = await event.get_message()
    with models.session_scope() as s:
        user = s.get(models.User, user_id)
        if data.startswith("confirm"):
            s.add(
                models.PlayerAccount(
                    user_id=user_id,
                    account_number=account_number.strip(),
                    registration_date=now_iso(),
                )
            )
            s.commit()
            await TeleClientSingleton().send_message(
                entity=user_id,
                message=TEXTS[user.lang]["account_link_success"],
            )
            await event.edit(
                text=msg.text,
                buttons=Button.inline(
                    "تمت الموافقة ✅",
                    "✅✅✅",
                ),
            )
        else:
            await event.edit(
                text=msg.text,
                buttons=Button.inline(
                    "تم الإلغاء ❌",
                    "❌❌❌",
                ),
            )
            await TeleClientSingleton().send_message(
                entity=user_id,
                message=TEXTS[user.lang]["account_not_reg"],
            )

    raise events.StopPropagation
