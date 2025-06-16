from telethon import events
from client.client_calls.client_calls import openai
from TeleClientSingleton import TeleClientSingleton
from Config import Config
import models
import utils.mobi_cash as mobi
import json
from sqlalchemy import and_


async def paste_receipte(event: events.NewMessage.Event):
    if event.chat_id != Config.RECEIPTS_GROUP_ID or not event.raw_text:
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
                "id": ...,
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
            existing_receipt = s.get(models.Receipt, parsed_receipt["id"])
            if not existing_receipt:
                amount = float(parsed_receipt["amount"])
                new_receipt = models.Receipt(
                    id=parsed_receipt["id"],
                    payment_method_id=parsed_receipt["payment_method_id"],
                    available_balance_at_the_time=parsed_receipt[
                        "available_balance_at_the_time"
                    ],
                    amount=amount,
                )
                transaction = (
                    s.query(models.Transaction)
                    .filter_by(receipt_id=parsed_receipt["id"])
                    .first()
                )
                if transaction and transaction.status == "pending":
                    res = await mobi.deposit(
                        user_id=transaction.user.player_account.account_number,
                        amount=amount,
                    )
                    if res["Success"]:
                        transaction.status = "approved"
                        transaction.mobi_operation_id = res['OperationId']
                        message = (
                            f"Deposit number <code>{transaction.id}</code> is done"
                        )
                    elif "Deposit limit exceeded" in res["Message"]:
                        message = "We're facing a technical problem with deposits at the moment so all deposit orders will be processed after about 5 minutes"
                    else:
                        transaction.status = "failed"
                        message = f"Deposit number <code>{transaction.id}</code> failed, reason: {res['Message']}"
                    new_receipt.transaction_id = transaction.id
                    transaction.amount = amount
                    await TeleClientSingleton().send_message(
                        entity=transaction.user_id,
                        message=message,
                        parse_mode="html",
                    )
                s.add(new_receipt)
                s.commit()
                await event.reply("تم ✅")
            await event.reply("مكرر ❗️")
        except json.decoder.JSONDecodeError:
            await event.reply("خطأ ❌")

    raise events.StopPropagation
