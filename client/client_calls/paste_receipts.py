from telethon import events
from client.client_calls.common import now_iso
from client.client_calls.constants import *
from client.client_calls.lang_dicts import *
from TeleClientSingleton import TeleClientSingleton
from Config import Config
import models
import utils.mobi_cash as mobi
import json
from sqlalchemy import and_
from user.buy_voucher.common import gift_voucher


async def paste_receipte(event: events.NewMessage.Event):
    if (not event.raw_text or event.sender_id != Config.PAYLINK_BOT_ID):
        return

    message_text = event.raw_text.strip()
    with models.session_scope() as s:
        payment_methods = (
            s.query(models.PaymentMethod)
            .filter(
                and_(
                    models.PaymentMethod.type.in_(["deposit", "both"]),
                    models.PaymentMethod.is_active == True,
                )
            )
            .all()
        )
        payment_methods_str = ", ".join(
            [f"PaymentMethod(id={p.id}, name={p.name})" for p in payment_methods]
        )
        # برومبت ملزم يطابق Receipt فقط
        prompt = (
            f"we have the following payment methods [{payment_methods_str}]\n"
            "Extract the following fields as JSON matching the Receipt table schema:\n"
            """
                {
                    "receipt_id": ...,
                    "payment_method_id": ...,
                    "amount": ...,
                    "available_balance_at_the_time": ...
                }
            """
            "Return only valid JSON and nothing else.\n\n"
            "Message to parse:\n"
            f"{message_text}"
        )

        # طلب من OpenAI ChatGPT
        resp = await openai.chat.completions.create(
            model=Config.GPT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant for financial operations.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=256,
            temperature=0,
        )
        content = resp.choices[0].message.content.strip()
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            parsed_receipt = json.loads(content)
            missing = []
            for k, v in parsed_receipt.items():
                if not v:
                    missing.append(k)
            if missing:
                await event.reply(f"Missing Fields {", ".join(missing)}")
                return
            existing_receipt = s.get(models.Receipt, parsed_receipt["receipt_id"])
            if not existing_receipt:
                amount = float(parsed_receipt["amount"])
                new_receipt = models.Receipt(
                    id=parsed_receipt["receipt_id"],
                    payment_method_id=parsed_receipt["payment_method_id"],
                    available_balance_at_the_time=parsed_receipt[
                        "available_balance_at_the_time"
                    ],
                    amount=amount,
                )
                transaction = (
                    s.query(models.Transaction)
                    .filter_by(receipt_id=parsed_receipt["receipt_id"])
                    .first()
                )
                if transaction and transaction.status == "pending":
                    new_receipt.transaction_id = transaction.id
                    transaction.amount = amount
                    player_account = (
                        s.query(models.PlayerAccount)
                        .filter_by(account_number=transaction.account_number)
                        .first()
                    )
                    res = await mobi.deposit(
                        user_id=transaction.account_number,
                        amount=amount,
                        country=player_account.country,
                    )
                    if res["Success"]:
                        transaction.status = "approved"
                        transaction.mobi_operation_id = res["OperationId"]
                        transaction.completed_at = now_iso()
                        s.commit()
                        message = (
                            f"Deposit number <code>{transaction.id}</code> is done"
                        )
                        offer_progress = player_account.check_offer_progress(s=s)
                        if offer_progress.get("completed", False):
                            player_account.offer_completed = True
                            offer_tx = models.Transaction.add_offer_transaction(
                                s=s, player_account=player_account
                            )
                            offer_dp = await mobi.deposit(
                                user_id=player_account.account_number,
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
                                message=TEXTS[transaction.user.lang][
                                    "offer_completed_msg"
                                ],
                            )
                        elif offer_progress.get("completed", None) is not None:
                            message += TEXTS[transaction.user.lang][
                                "progress_msg"
                            ].format(
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
                    if (player_account.currency == "aed" and amount >= 100) or (
                        player_account.currency == "syr" and amount >= 100_000
                    ):
                        await gift_voucher(
                            uid=transaction.user_id, s=s, lang=transaction.user.lang
                        )
                    await TeleClientSingleton().send_message(
                        entity=transaction.user_id,
                        message=message,
                        parse_mode="html",
                    )
                s.add(new_receipt)
                s.commit()
                await event.reply("تم ✅")
                return
            await event.reply("مكرر ❗️")
        except json.decoder.JSONDecodeError:
            await event.reply("خطأ ❌")

    raise events.StopPropagation
