import os
import models
import re
import pytesseract
from datetime import datetime, timezone
import time
from langdetect import detect
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
import logging

log = logging.getLogger(__name__)

openai = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)


def now_iso() -> datetime:
    return datetime.now(timezone.utc)


def classify_intent(text: str):
    t = (text or "").lower()
    if any(k in t for k in ("dp", "deposit", "ايداع")):
        return "Deposit"
    if any(k in t for k in ("wd", "withdraw", "سحب")):
        return "Withdraw"
    return None


def parse_receipt_text(text: str):

    result = {"amount": None, "transaction_id": None, "method": None, "date": None}

    cleaned_text = re.sub(r"[^\w\s\d.:/-]", "", text)

    amount_pattern = r"(?:مبلغ|amount|total|قيمة|value|مبلغ العملية)[:\s]*([\d,.]+)\s*(?:USD|SAR|AED|دولار|ريال|جنيه|درهم)?|(\d+[\.,]\d+\s*(?:USD|SAR|AED|دولار|ريال|جنيه|درهم))"
    transaction_id_pattern = r"(?:رقم العملية|transaction id|رقم المعاملة|ref|reference|رقم|معرف العملية|المرجعي)[:\s]*([\w-]+)"
    method_pattern = r"(?:الوسيلة|method|طريقة الدفع|طريقة|payment|via|بواسطة|paid by)[:\s]*(Visa|MasterCard|Bank Transfer|PayPal|تحويل بنكي|حوالة بنكية|حساب بنكي|[\w\s]+)|(\b(?:Visa|MasterCard|PayPal|تحويل بنكي|حوالة بنكية|حساب بنكي|بطاقة|كاش)\b)"
    date_pattern = r"(?:التاريخ|date|تاريخ|issued on)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}\s+[جمايو|يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر]+\s+\d{4})|(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{2}/\d{2}/\d{4}|\d{4}\s+\d{2}\s+\d{2}|\d{2}-\d{2}-\d{4})"

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



async def extract_text_from_photo(event: events.NewMessage.Event):
    path = None
    try:
        path = await event.download_media(file="photo.jpg")
        
        from PIL import Image, ImageEnhance, ImageFilter

        img = Image.open(path).convert("L")
        img = img.filter(ImageFilter.SHARPEN)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.5)
        
        text = pytesseract.image_to_string(img, lang="ara").strip()

        if not text:
            log.warning("لم يتم استخراج أي نص من الصورة.")
            await event.reply(
                "عذرًا، لم يتم استخراج أي نص من الصورة. يرجى إرسال صورة أوضح بجودة عالية."
            )
            return None, None

        cleaned_text = re.sub(
            r"[^\w\s\d.:/-إأآابتثجحخدذرزسشصضطظعغفقكلمنهويةى]", "", text
        )

        parsed_details = parse_receipt_text(cleaned_text)
        log.info(f"النص المستخرج: {cleaned_text}")

        return cleaned_text, parsed_details

    except Exception as e:
        log.error(f"خطأ في OCR: {e}")
        await event.reply(
            "عذرًا، حدث خطأ أثناء معالجة الصورة. يرجى إرسال صورة أوضح أو التأكد من جودة الصورة."
        )
        return None, None

    finally:
        if path and os.path.exists(path):
            os.remove(path)

# async def extract_text_from_photo(event: events.NewMessage.Event):
#     try:
#         path = await event.download_media(file="photo.jpg")
#         from PIL import Image, ImageEnhance, ImageFilter

#         img = Image.open(path).convert("L")
#         img = img.filter(ImageFilter.SHARPEN)
#         enhancer = ImageEnhance.Contrast(img)
#         img = enhancer.enhance(2.5)
#         img.save(path)
#         result = ocr_reader.readtext(
#             path,
#             detail=0,
#             paragraph=True,
#             contrast_ths=0.1,
#             adjust_contrast=0.9,
#             text_threshold=0.85,
#             low_text=0.2,
#         )
#         text = "\n".join(result).strip()
#         if not text:
#             log.warning("لم يتم استخراج أي نص من الصورة.")
#             await event.reply(
#                 "عذرًا، لم يتم استخراج أي نص من الصورة. يرجى إرسال صورة أوضح بجودة عالية."
#             )
#             return None, None
#         cleaned_text = re.sub(
#             r"[^\w\s\d.:/-إأآابتثجحخدذرزسشصضطظعغفقكلمنهويةى]", "", text
#         )
#         parsed_details = await parse_receipt_text(cleaned_text)
#         log.info(f"النص المستخرج: {cleaned_text}")
#         return cleaned_text, parsed_details
#     except Exception as e:
#         log.error(f"خطأ في OCR: {e}")
#         await event.reply(
#             "عذرًا، حدث خطأ أثناء معالجة الصورة. يرجى إرسال صورة أوضح أو التأكد من جودة الصورة."
#         )
#         return None, None
#     finally:
#         if path and os.path.exists(path):
#             os.remove(path)


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


async def gpt_reply(uid: int, st: str, msg: str = None) -> str:
    with models.session_scope() as s:
        prompt = s.get(models.Setting, "gpt_prompt").value
        s_msgs = (
            s.query(models.SessionMessage)
            .filter(
                models.SessionMessage.user_id == uid
                and models.SessionMessage.session_type == st
            )
            .order_by(models.SessionMessage.timestamp)
            .limit(10)
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
            try:
                lang = detect(msg)
                log.info(f"تم اكتشاف لغة الرسالة: {lang}")
            except Exception:
                lang = "en"
            msgs.append({"role": "user", "content": msg})
        try:
            resp = await openai.chat.completions.create(
                model=Config.GPT_MODEL, messages=msgs, temperature=0.7
            )
            reply = resp.choices[0].message.content.strip()
            save_message(uid, st, "assistant", reply, s)
            return reply
        except Exception as e:
            log.error(f"خطأ في استدعاء OpenAI API: {e}")
            return "Sorry, an error occurred while processing your request. Please try again later."


async def get_or_create_session(uid: int, st: str):
    with models.session_scope() as s:
        user_session = s.get(models.UserSession, uid)
        if user_session:
            try:
                await TeleClientSingleton().get_entity(user_session.group_id)
                if user_session.session_type != st:
                    try:
                        await TeleClientSingleton()(
                            EditTitleRequest(
                                user_session.group_id,
                                f"{st} – {user_session.user.name}",
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
                    title=f"{st} – {user.name}",
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
                peer,
                await TeleClientSingleton().get_entity(uid),
                ChatBannedRights(until_date=None, view_messages=True),
            )
        )
        await TeleClientSingleton()(LeaveChannelRequest(peer))

        log.info(f"تم طرد المستخدم {uid} والمدير {Config.ADMIN_ID} من المجموعة {gid}.")
    except Exception as e:
        log.error(f"خطأ أثناء الطرد: {e}")


async def session_timer(gid: int, uid: int, duration: int = 900):
    await asyncio.sleep(duration)
    await kick_user_and_admin(gid, uid)


async def start_session(uid: int, st: str):
    tg_user = await TeleClientSingleton().get_entity(uid)
    try:
        with models.session_scope() as s:
            user = s.get(models.User, uid)
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
            is_user_blacklisted = s.get(models.Blacklist, uid)
            if is_user_blacklisted:
                await TeleClientSingleton().send_message(
                    uid,
                    "عذرًا، تم إضافتك إلى القائمة السوداء بسبب محاولات احتيال متكررة.",
                )
                return
        gid, is_new = await get_or_create_session(uid, st)
        peer = await TeleClientSingleton().get_entity(gid)
        if is_new:
            welcome = await gpt_reply(uid, st, "")
            msg = await TeleClientSingleton().send_message(peer, welcome)
            try:
                await TeleClientSingleton().pin_message(peer, msg, notify=False)
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
                peer,
                [
                    tg_user,
                    await TeleClientSingleton().get_entity(Config.ADMIN_ID),
                ],
            )
        )
        inv = await TeleClientSingleton()(
            ExportChatInviteRequest(
                peer, expire_date=int(time.time()) + 3600, usage_limit=1
            )
        )
        await TeleClientSingleton().send_message(
            uid, f"🔗 Private {st} session link:\n{inv.link}"
        )
        if st == "Deposit":
            asyncio.create_task(session_timer(gid, uid))
    except ValueError as e:
        log.error(f"فشل في بدء الجلسة للمستخدم {uid} بسبب خطأ في الكيان: {e}")
        await TeleClientSingleton().send_message(
            uid,
            "Sorry, an error occurred while creating the session. Please try again later.",
        )
    except Exception as e:
        log.error(f"خطأ غير متوقع في بدء الجلسة للمستخدم {uid}: {e}")
        await TeleClientSingleton().send_message(
            uid,
            "Sorry, an error occurred while creating the session. Please try again later.",
        )
