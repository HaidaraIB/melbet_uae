from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from TeleClientSingleton import TeleClientSingleton
from telethon.tl.types import (
    ChannelParticipantAdmin,
    ChatParticipantAdmin,
    ChannelParticipantCreator,
    ChatParticipantCreator,
)
import utils.mobi_cash as mobi
from telethon.tl.functions.channels import EditBannedRequest
from common.constants import *
from telethon.tl.types import ChatBannedRights
from client.client_calls.common import openai
from Config import Config
import re
import logging
import models

log = logging.getLogger(__name__)


async def send_periodic_messages(context: ContextTypes.DEFAULT_TYPE):
    topic = context.job.data["topic"]
    with models.session_scope() as s:
        prompt = s.get(models.Setting, f"gpt_prompt_{topic}")
        default_prompt = s.get(models.Setting, "gpt_prompt")
        system = f"{prompt.value if prompt else default_prompt.value}"
    note = (
        (
            await openai.chat.completions.create(
                model=Config.GPT_MODEL,
                messages=[{"role": "user", "content": system}],
                temperature=0.3,
            )
        )
        .choices[0]
        .message.content.strip()
    )
    for chat_id in MONITOR_GROUPS:
        await context.bot.send_message(
            chat_id=chat_id,
            text=note,
            parse_mode=ParseMode.MARKDOWN,
        )


async def check_suspicious_users(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data["chat_id"]
    async for member in TeleClientSingleton().iter_participants(chat_id):
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
                monitor_group = await TeleClientSingleton().get_entity(entity=chat_id)
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


async def match_recipts_with_transaction(context: ContextTypes.DEFAULT_TYPE):
    with models.session_scope() as s:
        receipts = s.query(models.Receipt).all()
        for receipt in receipts:
            if receipt.transaction_id:
                continue
            transaction = (
                s.query(models.Transaction).filter_by(receipt_id=receipt.id).first()
            )
            if transaction and transaction.status == "pending":
                res = await mobi.deposit(
                    user_id=transaction.user.player_account.account_number,
                    amount=receipt.amount,
                )
                if res["Success"]:
                    message = f"Deposit number <code>{transaction.id}</code> is done"
                else:
                    message = f"Deposit number <code>{transaction.id}</code> failed, reason: {res['Message']}"
                receipt.transaction_id = transaction.id
                transaction.status = "approved"
                transaction.amount = receipt.amount
                await TeleClientSingleton().send_message(
                    entity=transaction.user_id,
                    message=message,
                    parse_mode="html",
                )
                s.commit()
