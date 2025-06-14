from telethon import events
from client.client_calls.client_calls import openai
from Config import Config
import models
import json


async def paste_receipte(event: events.NewMessage.Event):
    if event.chat_id != Config.RECEIPTS_GROUP_ID or not event.raw_text:
        return

    message_text = event.raw_text.strip()
    with models.session_scope() as s:
        payment_methods = s.query(models.PaymentMethod).filter_by(type="deposit").all()
        # برومبت ملزم يطابق Receipt فقط
        prompt = (
            f"we have the following payment methods [{", ".join([f"PaymentMethod(id={p.id}, name={p.name})" for p in payment_methods])}]\n"
            "Extract the following fields as JSON matching the Receipt table schema:\n"
            """
            {
                "id": ...,
                "payment_method_id": ...,
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
                new_receipt = models.Receipt(
                    id=parsed_receipt["id"],
                    payment_method_id=parsed_receipt["payment_method_id"],
                    available_balance_at_the_time=parsed_receipt[
                        "available_balance_at_the_time"
                    ],
                )
                s.add(new_receipt)
                s.commit()
                await event.reply("تم ✅")
            await event.reply("مكرر ❗️")
        except json.decoder.JSONDecodeError:
            await event.reply("خطأ ❌")
