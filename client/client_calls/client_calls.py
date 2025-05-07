from client.client_calls.common import (
    classify_intent,
    start_session,
    extract_text_from_photo,
    save_message,
    gpt_reply,
    kick_user_and_admin,
    now_iso,
    openai,
)
from Config import Config
import models
import re
from TeleClientSingleton import TeleClientSingleton
from telethon import events
import logging
from zoneinfo import ZoneInfo
from common.common import format_datetime

log = logging.getLogger(__name__)


async def client_handler(event: events.NewMessage.Event):
    cid = event.chat_id
    if cid == Config.MONITOR_GROUP_ID:
        uid = event.sender_id
        me = (await TeleClientSingleton().get_me()).id
        if uid in (me, Config.ADMIN_ID):
            return
        intent = classify_intent(event.raw_text)
        if not intent:
            return
        try:
            await event.delete()
        except Exception as e:
            log.error(f"خطأ في حذف الرسالة: {e}")
        try:
            note = (
                (
                    await openai.chat.completions.create(
                        model=Config.GPT_MODEL,
                        messages=[
                            {
                                "role": "system",
                                "content": f"Notify the team: User {uid} wants to {intent}",
                            }
                        ],
                        temperature=0.3,
                    )
                )
                .choices[0]
                .message.content.strip()
            )
            await TeleClientSingleton().send_message(Config.MONITOR_GROUP_ID, note)
        except Exception as e:
            log.error(f"خطأ في إنشاء إشعار OpenAI: {e}")
        await start_session(uid, intent)
        return

    try:
        ent = await TeleClientSingleton().get_entity(cid)
    except Exception as e:
        log.error(f"خطأ في جلب الكيان: {e}")
        return
    gid = ent.id
    with models.session_scope() as s:
        prompt = s.get(models.Setting, "gpt_prompt_session").value
        user_session = s.query(models.UserSession).filter_by(group_id=gid).first()
        if user_session and event.sender_id == user_session.user_id:
            uid, st = user_session.user_id, user_session.session_type
            if event.photo:
                extracted, parsed_details = await extract_text_from_photo(event)
                if extracted:
                    sender = await TeleClientSingleton().get_entity(uid)
                    sender_username = (
                        sender.username or sender.first_name or f"user_{uid}"
                    )

                    if re.search(
                        r"[^\w\s\d.:/-إأآابتثجحخدذرزسشصضطظعغفقكلمنهويةى]", extracted
                    ):
                        system_msg = "النظام: الإيصال يحتوي على أحرف غير واضحة. يرجى إرسال صورة أوضح بجودة عالية."
                        user_msg = (
                            f"المستخدم: أرسلت إيصال دفع. النص المستخرج:\n{extracted}"
                        )
                        save_message(uid, st, "system", system_msg, s)
                        save_message(uid, st, "user", user_msg, s)
                        reply = await gpt_reply(uid, st, prompt, user_msg)
                        await TeleClientSingleton().send_message(
                            cid, f"{system_msg}\n\n{reply}"
                        )
                        return

                    if not (
                        parsed_details["amount"] and parsed_details["transaction_id"]
                    ):
                        missing = [
                            k
                            for k, v in parsed_details.items()
                            if not v and k in ["amount", "transaction_id"]
                        ]
                        system_msg = f"النظام: لم نتمكن من استخراج التفاصيل الأساسية: {', '.join(missing)}.\nيرجى تقديم إيصال يتضمن المبلغ ورقم العملية على الأقل."
                        details_str = "\n".join(
                            [f"{k}: {v}" for k, v in parsed_details.items() if v]
                        )
                        user_msg = f"المستخدم: أرسلت إيصال دفع. التفاصيل المستخرجة:\n{details_str}"
                        save_message(uid, st, "system", system_msg, s)
                        save_message(uid, st, "user", user_msg, s)
                        reply = await gpt_reply(uid, st, prompt, user_msg)
                        await TeleClientSingleton().send_message(
                            cid, f"{system_msg}\n\n{reply}"
                        )
                        return

                    missing_optional = [
                        k
                        for k, v in parsed_details.items()
                        if not v and k in ["method", "date"]
                    ]
                    if missing_optional:
                        log.info(f"تفاصيل اختيارية مفقودة: {missing_optional}")

                    transaction_id = parsed_details["transaction_id"]
                    duplicate = (
                        s.query(models.PaymentText)
                        .filter(models.PaymentText.transaction_id == transaction_id)
                        .first()
                    )
                    if duplicate and duplicate.user_id != uid:
                        orig_uid, orig_username, orig_text, used_at = (
                            duplicate.user_id,
                            duplicate.username,
                            duplicate.text,
                            format_datetime(
                                duplicate.timestamp.astimezone(ZoneInfo("Asia/Dubai"))
                            ),
                        )
                        s.add(
                            models.FraudLog(
                                user_id=uid,
                                username=sender_username,
                                copied_from_id=orig_uid,
                                copied_from_username=orig_username,
                                timestamp=now_iso(),
                                receipt_text=extracted,
                                transaction_id=transaction_id,
                            )
                        )
                        s.commit()
                        count = s.query(models.FraudLog).filter_by(user_id=uid).count()
                        if count >= 5:
                            s.add(
                                models.Blacklist(
                                    user_id=uid,
                                    username=sender_username,
                                    timestamp=now_iso(),
                                )
                            )
                            s.commit()
                            system_msg = f"النظام: تم اكتشاف محاولة احتيال. هذه العملية (رقم العملية: {transaction_id}) استخدمها في الأصل المستخدم @{orig_username} ({orig_uid}) في {used_at}. هذه محاولتك رقم {count}. لقد تم إضافتك إلى القائمة السوداء."
                            save_message(uid, st, "system", system_msg, s)
                            await TeleClientSingleton().send_message(cid, system_msg)
                            admin_msg = f"🚨 مستخدم في القائمة السوداء:\n- المستخدم: {sender_username} ({uid})\n- الإيصال الأصلي: @{orig_username} ({orig_uid})\n- رقم العملية: {transaction_id}\n- التاريخ: {used_at}\n- عدد المحاولات: {count}\n- النص:\n{orig_text}"
                            await TeleClientSingleton().send_message(
                                Config.ADMIN_ID, admin_msg
                            )
                            return
                        system_msg = f"النظام: تم اكتشاف محاولة احتيال. هذه العملية (رقم العملية: {transaction_id}) استخدمها في الأصل المستخدم @{orig_username} ({orig_uid}) في {used_at}. هذه محاولتك رقم {count}. للعلم، في حال وصول عدد المحاولات إلى 5، سيتم إنهاء التعامل معك وإضافتك إلى القائمة السوداء."
                        save_message(uid, st, "system", system_msg, s)
                        admin_msg = f"🚨 محاولة احتيال:\n- المستخدم: {sender_username} ({uid})\n- الإيصال الأصلي: @{orig_username} ({orig_uid})\n- رقم العملية: {transaction_id}\n- التاريخ: {used_at}\n- عدد المحاولات: {count}\n- النص:\n{orig_text}"
                        await TeleClientSingleton().send_message(
                            Config.ADMIN_ID, admin_msg
                        )
                        reply = await gpt_reply(uid, st, prompt)
                        await TeleClientSingleton().send_message(
                            cid, f"{system_msg}\n\n{reply}"
                        )
                    else:
                        if not duplicate:
                            s.add(
                                models.PaymentText(
                                    user_id=uid,
                                    session_type=st,
                                    text=extracted,
                                    username=sender_username,
                                    transaction_id=transaction_id,
                                    timestamp=now_iso(),
                                )
                            )
                            s.commit()
                        details_str = "".join(
                            [f"{k}: {v}\n" for k, v in parsed_details.items() if v]
                        )
                        system_msg = (
                            f"النظام: تم التحقق من الإيصال بنجاح:\n{details_str}"
                        )
                        if missing_optional:
                            system_msg += f"ملاحظة: التفاصيل التالية مفقودة: {', '.join(missing_optional)}. يُرجى تقديمها يدويًا إذا أمكن.\n"
                        system_msg += "يرجى تقديم رقم حسابك في MELBET لمعالجة الإيداع."
                        user_msg = f"المستخدم: أرسلت إيصال دفع. التفاصيل المستخرجة:\n{details_str}"
                        save_message(uid, st, "system", system_msg, s)
                        save_message(uid, st, "user", user_msg, s)
                        reply = await gpt_reply(uid, st, prompt, user_msg)
                        await TeleClientSingleton().send_message(
                            cid, f"{system_msg}\n\n{reply}"
                        )
            else:
                txt: str = event.raw_text or ""
                if txt:
                    account_pattern = r"^\d{6,10}$"
                    if re.match(account_pattern, txt.strip()):
                        sender = await TeleClientSingleton().get_entity(uid)
                        sender_username = (
                            sender.username or sender.first_name or f"user_{uid}"
                        )
                        existing_account = (
                            s.query(models.MelbetAccount)
                            .filter(models.MelbetAccount.user_id == uid)
                            .first()
                        )
                        if existing_account and existing_account.user_id != uid:
                            system_msg = f"هذا الحساب {txt.strip()} عائد لمستخدم آخر"
                            save_message(uid, st, "system", system_msg, s)
                            await TeleClientSingleton().send_message(cid, system_msg)
                        elif existing_account:
                            count = (
                                s.query(models.MelbetAccountChange)
                                .filter_by(user_id=uid)
                                .count()
                            )
                            if count >= 3:
                                system_msg = (
                                    "فشل تغيير الحساب ❗️\n"
                                    f"النظام: تم اكتشاف محاولات متكررة لتغيير رقم الحساب. هذه محاولتك رقم {count}."
                                )
                                save_message(uid, st, "system", system_msg, s)
                                await TeleClientSingleton().send_message(
                                    cid, system_msg
                                )
                                return
                            default_account = existing_account.account_number
                            existing_account.account_number = txt.strip()
                            s.add(
                                models.MelbetAccountChange(
                                    user_id=uid,
                                    username=sender_username,
                                    old_account=default_account,
                                    new_account=txt.strip(),
                                    timestamp=now_iso(),
                                )
                            )
                            s.commit()

                            system_msg = f"تم تحديث الحساب الخاص بك من {existing_account.account_number} إلى {txt.strip()}. هذه محاولتك رقم {count + 1}"
                            save_message(uid, st, "system", system_msg, s)
                            reply = await gpt_reply(uid, st, prompt, system_msg)
                            await TeleClientSingleton().send_message(
                                cid, f"{system_msg}\n\n{reply}"
                            )
                        else:
                            s.add(
                                models.MelbetAccount(
                                    user_id=uid,
                                    account_number=txt.strip(),
                                    username=sender_username,
                                    timestamp=now_iso(),
                                )
                            )
                            s.commit()
                            system_msg = f"النظام: تم حفظ رقم حساب MELBET {txt.strip()} بنجاح. جاري معالجة الإيداع."
                            save_message(uid, st, "system", system_msg, s)
                            reply = await gpt_reply(uid, st, prompt, system_msg)
                            await TeleClientSingleton().send_message(
                                cid, f"{system_msg}\n\n{reply}"
                            )
                    else:
                        save_message(uid, st, "user", txt, s)
                        reply = await gpt_reply(uid, st, prompt, txt)
                        await TeleClientSingleton().send_message(cid, reply)


async def end_session(event: events.NewMessage.Event):
    cid = event.chat_id
    try:
        ent = await TeleClientSingleton().get_entity(cid)
    except Exception as e:
        log.error(f"خطأ في جلب الكيان: {e}")
        return
    gid = ent.id
    with models.session_scope() as s:
        user_session = s.query(models.UserSession).filter_by(group_id=gid).first()
        if user_session:
            await kick_user_and_admin(
                gid=user_session.group_id, uid=user_session.user_id
            )
