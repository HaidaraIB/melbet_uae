from telegram.ext import ContextTypes
from TeleClientSingleton import TeleClientSingleton
from telethon.tl.types import (
    ChannelParticipantAdmin,
    ChatParticipantAdmin,
    ChannelParticipantCreator,
    ChatParticipantCreator,
)
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
from Config import Config
import re
import logging

log = logging.getLogger(__name__)


async def check_suspicious_users(context: ContextTypes.DEFAULT_TYPE):
    async for member in TeleClientSingleton().iter_participants(
        Config.MONITOR_GROUP_ID
    ):
        if isinstance(
            member.participant,
            (
                ChannelParticipantAdmin,
                ChatParticipantAdmin,
                ChannelParticipantCreator,
                ChatParticipantCreator,
            ),
        ):
            continue

        is_scammer = contains_restricted_word(
            f"{member.first_name} {member.last_name if member.last_name else ''} {member.username if member.username else ''}"
        )
        if is_scammer:
            try:
                monitor_group = await TeleClientSingleton().get_entity(Config.MONITOR_GROUP_ID)
                await TeleClientSingleton()(
                    EditBannedRequest(
                        channel=monitor_group,
                        participant=await TeleClientSingleton().get_entity(member.id),
                        banned_rights=ChatBannedRights(until_date=None, view_messages=True),
                    )
                )
                log.info(f"تم طرد المستخدم {member.id} من مجموعة المراقبة.")
            except Exception as e:
                log.error(f"خطأ أثناء الطرد: {e}")


def contains_restricted_word(text: str):
    restricted_words = [
        r"melbet",
        r"mel\-bet",
        r"mel bet",
        r"mlbet",
        r"me1bet",
        r"m3lbet",
        r"melbett",
        r"meIbet",
        r"m€lbet",
        r"mèlbet",
        r"міlbet",
        r"ملبت",
        r"ميلبت",
        r"مل\-بيت",
        r"manager",
        r"manger",
        r"mngr",
        r"m4nager",
        r"manag3r",
        r"manag3r25628",
        r"manager256",
        r"mgr25628",
        r"25628manager",
        r"manager_25628",
        r"manager\-25628",
        r"manâger",
        r"månager",
        r"ȼmanager",
    ]
    pattern = r"(?:" + "|".join(restricted_words) + r")"
    match = re.search(pattern, text, re.IGNORECASE)
    return match is not None
