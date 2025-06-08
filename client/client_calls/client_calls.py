from client.client_calls.common import (
    classify_intent,
    start_session,
    extract_text_from_photo,
    save_message,
    gpt_reply,
    kick_user_and_admin,
    now_iso,
    add_or_update_account,
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
from client.client_calls.lang_dicts import *

log = logging.getLogger(__name__)


async def listen_to_dp_and_wd_requests(event: events.NewMessage.Event):
    uid = event.sender_id
    sender = await TeleClientSingleton().get_permissions(
        entity=Config.MONITOR_GROUP_ID, user=uid
    )
    if sender.is_admin:
        return
    intent = classify_intent(event.raw_text)
    if not intent:
        return
    try:
        await event.delete()
    except Exception as e:
        log.error(f"خطأ في حذف الرسالة: {e}")
    try:
        with models.session_scope() as s:
            default_prompt = s.get(models.Setting, "gpt_prompt")
            monitor_prompt = s.get(models.Setting, "gpt_prompt_monitor")
            note = (
                (
                    await openai.chat.completions.create(
                        model=Config.GPT_MODEL,
                        messages=[
                            {
                                "role": "user",
                                "content": (
                                    monitor_prompt.value
                                    if monitor_prompt
                                    else default_prompt.value
                                )
                                + f"User {uid} wants to {intent}",
                            },
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
    raise events.StopPropagation


async def respond_in_private(event: events.NewMessage.Event):
    if not event.is_private:
        return
    uid = event.sender_id
    sender = await TeleClientSingleton().get_entity(uid)
    with models.session_scope() as s:
        default_prompt = s.get(models.Setting, "gpt_prompt")
        if not s.get(models.User, uid) or sender.bot:
            return
        manager_prompt = s.get(models.Setting, f"gpt_prompt_manager")

        txt: str = event.raw_text or ""
        try:
            save_message(uid, "general", "user", txt, s)
            reply = await gpt_reply(
                uid=uid,
                st="general",
                prompt=(
                    manager_prompt.value if manager_prompt else default_prompt.value
                ),
                msg=txt,
            )
            await TeleClientSingleton().send_message(uid, reply)
        except Exception as e:
            log.error(f"Error while generally responding to user {uid}: {e}")
    raise events.StopPropagation


async def handle_session(event: events.NewMessage.Event):
    if not event.is_group:
        return
    cid = event.chat_id
    uid = event.sender_id
    ent = await TeleClientSingleton().get_entity(cid)
    with models.session_scope() as s:
        default_prompt = s.get(models.Setting, "gpt_prompt")
        user_session = s.query(models.UserSession).filter_by(group_id=ent.id).first()
        user = s.get(models.User, uid)
        if user_session and uid == user_session.user_id:
            sender = await TeleClientSingleton().get_entity(uid)
            user_account = s.query(models.MelbetAccount).filter_by(user_id=uid).first()
            if not user_account:
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=TEXTS[user.lang]["no_account"],
                )
                return
            st = user_session.session_type
            session_prompt = s.get(models.Setting, f"gpt_prompt_{st}")
            if event.photo:
                extracted, parsed_details = await extract_text_from_photo(
                    event=event, lang=user.lang
                )
                if extracted:
                    sender_username = (
                        sender.username or sender.first_name or f"user_{uid}"
                    )

                    if re.search(
                        r"[^\w\s\d.:/-إأآابتثجحخدذرزسشصضطظعغفقكلمنهويةى]", extracted
                    ):
                        system_msg = TEXTS[user.lang]["receipt_unclear_chars"]
                        user_msg = (
                            f"المستخدم: أرسلت إيصال دفع. النص المستخرج:\n{extracted}"
                        )
                        save_message(uid, st, "system", system_msg, s)
                        save_message(uid, st, "user", user_msg, s)
                        reply = await gpt_reply(
                            uid=uid,
                            st=st,
                            prompt=(
                                session_prompt.value
                                if session_prompt
                                else default_prompt.value
                            ),
                            msg=user_msg,
                        )
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
                        system_msg = TEXTS[user.lang][
                            "missing_essential_details"
                        ].format(", ".join(missing))

                        details_str = "\n".join(
                            [f"{k}: {v}" for k, v in parsed_details.items() if v]
                        )
                        user_msg = f"المستخدم: أرسلت إيصال دفع. التفاصيل المستخرجة:\n{details_str}"
                        save_message(uid, st, "system", system_msg, s)
                        save_message(uid, st, "user", user_msg, s)
                        reply = await gpt_reply(
                            uid=uid,
                            st=st,
                            prompt=(
                                session_prompt.value
                                if session_prompt
                                else default_prompt.value
                            ),
                            msg=user_msg,
                        )
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

                            system_msg = TEXTS[user.lang][
                                "fraud_detected_blacklisted"
                            ].format(
                                transaction_id, orig_username, orig_uid, used_at, count
                            )

                            save_message(uid, st, "system", system_msg, s)
                            await TeleClientSingleton().send_message(cid, system_msg)
                            admin_msg = f"🚨 مستخدم في القائمة السوداء:\n- المستخدم: {sender_username} ({uid})\n- الإيصال الأصلي: @{orig_username} ({orig_uid})\n- رقم العملية: {transaction_id}\n- التاريخ: {used_at}\n- عدد المحاولات: {count}\n- النص:\n{orig_text}"
                            await TeleClientSingleton().send_message(
                                Config.ADMIN_ID, admin_msg
                            )
                            return
                        system_msg = TEXTS[user.lang]["fraud_detected_warning"].format(
                            transaction_id, orig_username, orig_uid, used_at, count
                        )

                        save_message(uid, st, "system", system_msg, s)
                        admin_msg = f"🚨 محاولة احتيال:\n- المستخدم: {sender_username} ({uid})\n- الإيصال الأصلي: @{orig_username} ({orig_uid})\n- رقم العملية: {transaction_id}\n- التاريخ: {used_at}\n- عدد المحاولات: {count}\n- النص:\n{orig_text}"
                        await TeleClientSingleton().send_message(
                            Config.ADMIN_ID, admin_msg
                        )
                        reply = await gpt_reply(
                            uid=uid,
                            st=st,
                            prompt=(
                                session_prompt.value
                                if session_prompt
                                else default_prompt.value
                            ),
                        )
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
                        system_msg = TEXTS[user.lang][
                            "receipt_verified_success"
                        ].format(details_str)
                        if missing_optional:
                            system_msg += TEXTS[user.lang][
                                "missing_optional_details"
                            ].format(", ".join(missing_optional))

                        user_msg = f"المستخدم: أرسلت إيصال دفع. التفاصيل المستخرجة:\n{details_str}"
                        save_message(uid, st, "system", system_msg, s)
                        save_message(uid, st, "user", user_msg, s)
                        reply = await gpt_reply(
                            uid=uid,
                            st=st,
                            prompt=(
                                session_prompt.value
                                if session_prompt
                                else default_prompt.value
                            ),
                            msg=user_msg,
                        )
                        await TeleClientSingleton().send_message(
                            cid, f"{system_msg}\n\n{reply}"
                        )
            elif event.raw_text:
                txt: str = event.raw_text
                account_pattern = r"^\d{6,10}$"
                if re.match(account_pattern, txt.strip()):
                    pass
                    # await add_or_update_account(
                    #     account_number=txt,
                    #     cid=cid,
                    #     uid=uid,
                    #     s=s,
                    #     default_prompt=default_prompt,
                    #     session_prompt=session_prompt,
                    #     lang=user.lang,
                    #     st=st,
                    # )
                else:
                    save_message(uid, st, "user", txt, s)
                    reply = await gpt_reply(
                        uid=uid,
                        st=st,
                        prompt=(
                            session_prompt.value
                            if session_prompt
                            else default_prompt.value
                        ),
                        msg=txt,
                    )
                    await TeleClientSingleton().send_message(cid, reply)
    raise events.StopPropagation


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
    raise events.StopPropagation
