import os
import models
import re
from google.cloud import vision
from PIL import Image, ImageEnhance, ImageFilter
from datetime import datetime, timezone
import time
from TeleClientSingleton import TeleClientSingleton
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    InviteToChannelRequest,
    EditTitleRequest,
    EditBannedRequest,
    LeaveChannelRequest,
)
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.types import ChatBannedRights
from openai import AsyncOpenAI
from Config import Config
from telethon import events
import asyncio
from sqlalchemy.orm import Session
from client.client_calls.lang_dicts import *
import logging

log = logging.getLogger(__name__)

openai = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)


def now_iso() -> datetime:
    return datetime.now(timezone.utc)


def classify_intent(text: str):
    t = (text or "").lower()
    if any(k in t for k in ("dp", "deposit", "ايداع", "إيداع")):
        return "deposit"
    if any(k in t for k in ("wd", "withdraw", "سحب")):
        return "withdraw"
    return None


def parse_receipt_text(text: str):

    result = {"amount": None, "transaction_id": None, "method": None, "date": None}

    cleaned_text = re.sub(r"[^\w\s\d.:/-]", "", text)

    amount_pattern = r"(?:مبلغ|amount|total|total payment|قيمة|value|مبلغ العملية|إجمالي المبلغ|إجمالي المبلغ المقتطع)?[:\s]*(?:usd|sar|aed|دولار|ريال|جنيه|درهم)?\s*([\d,.]+)|([\d,.]+)\s*(?:usd|sar|aed|دولار|ريال|جنيه|درهم)"
    transaction_id_pattern = r"(?:رقم العملية|transaction id||رقم المعاملة|ref|reference|رقم|معرف العملية|الرقم المرجعي|المرجعي)[:\s]*([\w-]+)"
    method_pattern = r"(?:الوسيلة|method|طريقة الدفع|طريقة|payment method|via|بواسطة|paid by)[:\s]*(visa|masterCard|bank transfer|paypal|تحويل بنكي|حوالة بنكية|حساب بنكي|[\w\s]+)|(\b(?:visa|mastercard|paypal|تحويل بنكي|حوالة بنكية|حساب بنكي|بطاقة|كاش)\b)"
    date_pattern = r"(?:التاريخ|date|تاريخ|issued on|transfer time)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}\s+[جمايو|يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر]+\s+\d{4})|(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{2}/\d{2}/\d{4}|\d{4}\s+\d{2}\s+\d{2}|\d{2}-\d{2}-\d{4})"

    amount_match = re.search(amount_pattern, cleaned_text, re.IGNORECASE)
    if amount_match:
        result["amount"] = amount_match.group(1) or amount_match.group(2)

    transaction_id_match = re.search(
        transaction_id_pattern, cleaned_text, re.IGNORECASE
    )
    if transaction_id_match:
        result["transaction_id"] = transaction_id_match.group(1)

    method_match = re.search(method_pattern, cleaned_text, re.IGNORECASE)
    if method_match:
        result["method"] = method_match.group(1) or method_match.group(2)

    date_match = re.search(date_pattern, cleaned_text, re.IGNORECASE)
    if date_match:
        result["date"] = date_match.group(1) or date_match.group(2)

    if result["transaction_id"] in ["المرجعي", "رقم", "معرف"]:
        result["transaction_id"] = None

    if not any(result.values()):
        log.warning(f"فشل تحليل النص: {cleaned_text}")
    else:
        log.info(f"تم استخراج التفاصيل: {result}")

    return result


def is_financial_receipt(text: str) -> bool:
    keywords = [
        "مبلغ",
        "تحويل",
        "إيصال",
        "amount",
        "transaction",
        "payment",
        "deposit",
        "رقم العملية",
        "معرف العملية",
        "درهم",
    ]
    return any(keyword.lower() in text.lower() for keyword in keywords)



async def extract_text_from_photo(event, lang):
    path = None
    photo_name = "photo.jpg"
    try:
        # تحميل الصورة من تيليجرام
        path = await event.download_media(file=photo_name)
        
        # (اختياري) معالجة الصورة للتوضيح، إذا أردت
        img = Image.open(path).convert("L")
        img = img.filter(ImageFilter.SHARPEN)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.5)
        img.save(photo_name)
        img_path_to_send = photo_name

        # إنشاء عميل Google Vision
        client = vision.ImageAnnotatorClient()
        with open(img_path_to_send, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations

        if not texts:
            log.warning("لم يتم استخراج أي نص من الصورة.")
            await event.reply(TEXTS[lang]["no_text_extracted_from_photo"])
            return None, None

        text = texts[0].description.strip()
        cleaned_text = re.sub(
            r"[^\w\s\d.:/-إأآابتثجحخدذرزسشصضطظعغفقكلمنهويةى]", "", text
        )

        parsed_details = parse_receipt_text(cleaned_text.lower())
        log.info(f"النص المستخرج: {cleaned_text}")
        return cleaned_text, parsed_details

    except Exception as e:
        log.error(f"خطأ في OCR (Google Vision): {e}")
        await event.reply(
            "عذرًا، حدث خطأ أثناء معالجة الصورة (Google OCR). يرجى إرسال صورة أوضح أو التأكد من جودة الصورة."
        )
        return None, None

    finally:
        if path and os.path.exists(path):
            os.remove(path)


def save_message(uid: int, st: str, role: str, msg: str, s: Session):
    valid_roles = {"system", "assistant", "user"}
    if role not in valid_roles:
        log.warning(f"دور غير صالح: {role}، يتم تعيينه إلى 'user'")
        role = "user"
    s.add(
        models.SessionMessage(
            user_id=uid,
            session_type=st,
            role=role,
            message=msg,
            timestamp=now_iso(),
        )
    )
    s.commit()


async def gpt_reply(uid: int, st: str, prompt: str, msg: str = None) -> str:
    with models.session_scope() as s:
        s_msgs = (
            s.query(models.SessionMessage)
            .filter(
                models.SessionMessage.user_id == uid
                and models.SessionMessage.session_type == st
            )
            .order_by(models.SessionMessage.timestamp)
            .limit(20)
            .all()
        )
        valid_roles = {"system", "assistant", "user"}
        history = [
            {"role": msg.role, "content": msg.message}
            for msg in reversed(s_msgs)
            if msg.role in valid_roles and msg.message is not None
        ]
        system = f"{prompt}\n(This is a private session for {st})"
        msgs = [{"role": "system", "content": system}] + history
        if msg:
            msgs.append({"role": "user", "content": msg})
        try:
            resp = await openai.chat.completions.create(
                model=Config.GPT_MODEL,
                messages=msgs,
                temperature=0.7,
            )
            reply = resp.choices[0].message.content.strip()
            save_message(uid, st, "assistant", reply, s)
            return reply
        except Exception as e:
            log.error(f"خطأ في استدعاء OpenAI API: {e}")
            return "Sorry, an error occurred while processing your request. Please try again later."


async def get_or_create_session(uid: int, st: str, s: Session):
    user_session = s.get(models.UserSession, uid)
    if user_session:
        try:
            await TeleClientSingleton().get_entity(user_session.group_id)
            if user_session.session_type != st:
                try:
                    user: models.User = user_session.user
                    await TeleClientSingleton()(
                        EditTitleRequest(
                            channel=user_session.group_id,
                            title=f"{st} – {user.username if user.username else user.name}",
                        )
                    )
                except Exception as e:
                    log.error(f"خطأ في تعديل عنوان القناة: {e}")
                user_session.session_type = st
            user_session.last_active = now_iso()
            s.commit()
            return user_session.group_id, False
        except ValueError as e:
            log.warning(
                f"معرف المجموعة {user_session.group_id} غير صالح للمستخدم {uid}: {e}. إنشاء مجموعة جديدة."
            )
            s.query(models.UserSession).filter(
                models.UserSession.user_id == uid
            ).delete()
            s.commit()

    try:
        user = s.get(models.User, uid)
        res = await TeleClientSingleton()(
            CreateChannelRequest(
                title=f"{st} – {user.username if user.username else user.name}",
                about=f"جلسة {st} للمستخدم {uid}",
                megagroup=True,
            )
        )
        chat = res.chats[0]
        gid = chat.id
        with models.session_scope() as s:
            s.add(
                models.UserSession(
                    user_id=uid,
                    group_id=gid,
                    session_type=st,
                    last_active=now_iso(),
                    created_at=now_iso(),
                )
            )
            s.commit()
        return gid, True
    except Exception as e:
        log.error(f"خطأ في إنشاء المجموعة: {e}")
        raise


async def kick_user_and_admin(gid: int, uid: int):
    try:
        peer = await TeleClientSingleton().get_entity(gid)
        await TeleClientSingleton()(
            EditBannedRequest(
                channel=peer,
                participant=await TeleClientSingleton().get_entity(uid),
                banned_rights=ChatBannedRights(until_date=None, view_messages=True),
            )
        )
        await TeleClientSingleton()(LeaveChannelRequest(channel=peer))

        log.info(f"تم طرد المستخدم {uid} والمدير {Config.ADMIN_ID} من المجموعة {gid}.")
    except Exception as e:
        log.error(f"خطأ أثناء الطرد: {e}")


async def session_timer(gid: int, uid: int, duration: int = 900):
    timer = models.SessionTimer(uid=uid, gid=gid, end_time=int(time.time()) + duration)
    with models.session_scope() as s:
        s.merge(timer)
        s.commit()
    await asyncio.sleep(duration)
    await kick_user_and_admin(gid, uid)
    with models.session_scope() as s:
        s.query(models.SessionTimer).filter(
            models.SessionTimer.uid == uid, models.SessionTimer.gid == gid
        ).delete()
        s.commit()


async def resume_timers_on_startup():
    with models.session_scope() as s:
        timers = s.query(models.SessionTimer).all()
        for timer in timers:
            remaining_time = timer.end_time - int(time.time())
            if remaining_time > 0:
                asyncio.create_task(session_timer(timer.gid, timer.uid, remaining_time))
                log.info(f"session timer {timer} resumed.")
            else:
                await kick_user_and_admin(timer.gid, timer.uid)
                s.query(models.SessionTimer).filter(
                    models.SessionTimer.uid == timer.uid,
                    models.SessionTimer.gid == timer.gid,
                ).delete()
                s.commit()
                log.info(f"session timer {timer} triggered.")


async def start_session(uid: int, st: str):
    tg_user = await TeleClientSingleton().get_entity(uid)
    with models.session_scope() as s:
        user = s.get(models.User, uid)
        try:
            if not user:
                user = models.User(
                    user_id=tg_user.id,
                    username=tg_user.username if tg_user.username else "",
                    name=(
                        (tg_user.first_name + tg_user.last_name)
                        if tg_user.last_name
                        else tg_user.first_name
                    ),
                )
                s.add(user)
                s.commit()
            is_user_blacklisted = s.get(models.Blacklist, uid)
            if is_user_blacklisted:
                await TeleClientSingleton().send_message(
                    entity=uid,
                    message=TEXTS[user.lang]["blacklisted_user"],
                )
                return
            gid, is_new = await get_or_create_session(uid, st, s)
            peer = await TeleClientSingleton().get_entity(gid)
            if is_new:
                welcome = await gpt_reply(uid, st, "")
                msg = await TeleClientSingleton().send_message(peer, welcome)
                end_cmd = await TeleClientSingleton().send_message(peer, "/end")
                try:
                    await TeleClientSingleton().pin_message(peer, msg, notify=False)
                    await TeleClientSingleton().pin_message(peer, end_cmd, notify=False)
                except Exception as e:
                    log.error(f"خطأ في تثبيت الرسالة: {e}")
            try:
                await TeleClientSingleton()(
                    EditBannedRequest(
                        peer,
                        tg_user,
                        ChatBannedRights(until_date=0, view_messages=False),
                    )
                )
            except Exception as e:
                log.error(f"خطأ في تعديل الأذونات: {e}")
            await TeleClientSingleton()(
                InviteToChannelRequest(
                    channel=peer,
                    users=[
                        tg_user,
                        await TeleClientSingleton().get_entity(Config.ADMIN_ID),
                    ],
                )
            )
            inv = await TeleClientSingleton()(
                ExportChatInviteRequest(
                    peer=peer,
                    expire_date=int(time.time()) + 3600,
                    usage_limit=1,
                )
            )
            await TeleClientSingleton().send_message(
                entity=uid,
                message=TEXTS[user.lang]["session_link"].format(st, inv.link),
            )
            if st == "deposit":
                asyncio.create_task(session_timer(gid, uid))
            else:
                with models.session_scope() as s:
                    s.query(models.SessionTimer).filter(
                        models.SessionTimer.uid == uid, models.SessionTimer.gid == gid
                    ).delete()
                    s.commit()
        except ValueError as e:
            log.error(f"فشل في بدء الجلسة للمستخدم {uid} بسبب خطأ في الكيان: {e}")
            await TeleClientSingleton().send_message(
                entity=uid,
                message=TEXTS[user.lang]["session_start_failed"],
            )
        except Exception as e:
            log.error(f"خطأ غير متوقع في بدء الجلسة للمستخدم {uid}: {e}")
            await TeleClientSingleton().send_message(
                entity=uid,
                message=TEXTS[user.lang]["unexpected_session_error"],
            )


async def add_or_update_account(
    uid: int,
    cid: int,
    account_number: str,
    st: str,
    session_prompt: models.Setting,
    default_prompt: models.Setting,
    lang,
    s: Session,
):
    sender = await TeleClientSingleton().get_entity(uid)
    sender_username = sender.username or sender.first_name or f"user_{uid}"
    existing_account = (
        s.query(models.MelbetAccount)
        .filter(models.MelbetAccount.user_id == uid)
        .first()
    )
    if existing_account and existing_account.user_id != uid:
        system_msg = TEXTS[lang]["account_belongs_another"].format(
            account_number.strip()
        )
        save_message(uid, st, "system", system_msg, s)
        await TeleClientSingleton().send_message(cid, system_msg)
    elif existing_account:
        count = s.query(models.MelbetAccountChange).filter_by(user_id=uid).count()
        if count >= 3:
            system_msg = TEXTS[lang]["account_change_failed"].format(count)
            save_message(uid, st, "system", system_msg, s)
            await TeleClientSingleton().send_message(cid, system_msg)
            return
        default_account = existing_account.account_number
        existing_account.account_number = account_number.strip()
        s.add(
            models.MelbetAccountChange(
                user_id=uid,
                username=sender_username,
                old_account=default_account,
                new_account=account_number.strip(),
                timestamp=now_iso(),
            )
        )
        s.commit()

        change_account_prompt = s.get(models.Setting, "gpt_prompt_change_account")

        system_msg = TEXTS[lang]["account_updated"].format(
            existing_account.account_number, account_number.strip(), count + 1
        )
        save_message(uid, st, "system", system_msg, s)
        reply = await gpt_reply(
            uid=uid,
            st=st,
            prompt=(
                change_account_prompt.value
                if change_account_prompt
                else default_prompt.value
            ),
            msg=system_msg,
        )
        await TeleClientSingleton().send_message(cid, f"{system_msg}\n\n{reply}")
    else:
        s.add(
            models.MelbetAccount(
                user_id=uid,
                account_number=account_number.strip(),
                username=sender_username,
                timestamp=now_iso(),
            )
        )
        s.commit()
        system_msg = TEXTS[lang]["account_saved"].format(account_number.strip())
        save_message(uid, st, "system", system_msg, s)
        reply = await gpt_reply(
            uid=uid,
            st=st,
            prompt=(session_prompt.value if session_prompt else default_prompt.value),
            msg=system_msg,
        )
        await TeleClientSingleton().send_message(cid, f"{system_msg}\n\n{reply}")
