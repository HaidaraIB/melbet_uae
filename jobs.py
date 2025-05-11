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
from client.client_calls.common import openai
from Config import Config
import re
import logging
import models
import requests
from datetime import datetime, timedelta

log = logging.getLogger(__name__)


async def send_periodic_messages(context: ContextTypes.DEFAULT_TYPE):
    with models.session_scope() as s:
        prompt = s.get(models.Setting, f"gpt_prompt_{context.job.data}")
        default_prompt = s.get(models.Setting, "gpt_prompt")
        system = f"{prompt.value if prompt else default_prompt.value}"
    note = (
        (
            await openai.chat.completions.create(
                model=Config.GPT_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": system,
                    }
                ],
                temperature=0.3,
            )
        )
        .choices[0]
        .message.content.strip()
    )
    await context.bot.send_message(chat_id=Config.MONITOR_GROUP_ID, text=note)


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
                monitor_group = await TeleClientSingleton().get_entity(
                    Config.MONITOR_GROUP_ID
                )
                await TeleClientSingleton()(
                    EditBannedRequest(
                        channel=monitor_group,
                        participant=await TeleClientSingleton().get_entity(member.id),
                        banned_rights=ChatBannedRights(
                            until_date=None, view_messages=True
                        ),
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


async def schedule_pre_match_lineups(matches, context: ContextTypes.DEFAULT_TYPE):
    for match in matches:
        # Schedule lineup posting 55 minutes before match
        lineup_time: datetime = match["start_time"] - timedelta(minutes=55)

        context.job_queue.run_once(
            callback=send_lineups,
            when=(lineup_time - datetime.now()).total_seconds(),
            data=match,
        )


async def send_lineups(context: ContextTypes.DEFAULT_TYPE):
    match = context.job.data
    # Replace with your lineup API call
    home_lineup = "Team A Lineup:\nPlayer1\nPlayer2\n..."
    away_lineup = "Team B Lineup:\nPlayer1\nPlayer2\n..."

    message = (
        f"⚠️ <b>Lineups for {match['home_team']} vs {match['away_team']}</b> ⚠️\n\n"
        f"{home_lineup}\n\n"
        f"{away_lineup}\n\n"
        f"⏰ Match starts at <code>{match['start_time'].strftime('%H:%M')}</code>"
    )

    await context.bot.send_message(
        chat_id=Config.MONITOR_GROUP_ID,
        text=message,
    )
