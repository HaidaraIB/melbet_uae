from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from TeleClientSingleton import TeleClientSingleton
from telethon.tl.types import (
    ChannelParticipantAdmin,
    ChatParticipantAdmin,
    ChannelParticipantCreator,
    ChatParticipantCreator,
)
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
import utils.mobi_cash as mobi
from common.constants import *
from user.buy_voucher.common import gift_voucher
from client.client_calls.common import now_iso
from client.client_calls.lang_dicts import *
from client.client_calls.constants import *
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
            transaction = (
                s.query(models.Transaction).filter_by(receipt_id=receipt.id).first()
            )
            if not transaction or (
                receipt.transaction_id
                and transaction.status in ["approved", "declined"]
            ):
                continue
            elif transaction.status in ["failed", "pending"]:
                receipt.transaction_id = transaction.id
                transaction.amount = receipt.amount
                player_account = (
                    s.query(models.PlayerAccount)
                    .filter_by(account_number=transaction.account_number)
                    .first()
                )
                res = await mobi.deposit(
                    user_id=transaction.account_number,
                    amount=receipt.amount,
                    country=player_account.country,
                )
                if res["Success"]:
                    transaction.status = "approved"
                    transaction.mobi_operation_id = res["OperationId"]
                    transaction.completed_at = now_iso()
                    s.commit()
                    message = f"Deposit number <code>{transaction.id}</code> is done"
                    offer_progress = player_account.check_offer_progress(s=s)
                    if offer_progress.get("completed", False):
                        player_account.offer_completed = True
                        offer_tx = models.Transaction.add_offer_transaction(
                            s=s, player_account=player_account
                        )
                        offer_dp = await mobi.deposit(
                            user_id=transaction.account_number,
                            amount=player_account.offer_prize,
                            country=player_account.country,
                        )
                        if offer_dp["Success"]:
                            offer_tx.status = "approved"
                            offer_tx.mobi_operation_id = res["OperationId"]
                            offer_tx.completed_at = now_iso()
                        else:
                            offer_tx.status = "failed"
                            offer_tx.fail_reason = res["Message"]
                        await TeleClientSingleton().send_message(
                            entity=transaction.user_id,
                            message=TEXTS[transaction.user.lang]["offer_completed_msg"],
                        )
                    elif offer_progress.get("completed", None) is not None:
                        message += TEXTS[transaction.user.lang]["progress_msg"].format(
                            offer_progress["amount_left"],
                            player_account.currency,
                            offer_progress["deposit_days_left"],
                            player_account.offer_expiry_date,
                        )
                else:
                    transaction.status = "failed"
                    transaction.fail_reason = res["Message"]
                    if "Deposit limit exceeded" in res["Message"]:
                        message = "We're facing a technical problem with deposits at the moment so all deposit orders will be processed after about 5 minutes"
                    else:
                        message = f"Deposit number <code>{transaction.id}</code> failed, reason: {res['Message']}"
                if (player_account.currency == "aed" and receipt.amount >= 100) or (
                    player_account.currency == "syr" and receipt.amount >= 100_000
                ):
                    await gift_voucher(
                        uid=transaction.user_id, s=s, lang=transaction.user.lang
                    )
                await TeleClientSingleton().send_message(
                    entity=transaction.user_id,
                    message=message,
                    parse_mode="html",
                )
                s.commit()
