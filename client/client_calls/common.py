import os
import models
import re
from google.cloud import vision
from PIL import Image, ImageEnhance, ImageFilter
import time
from TeleClientSingleton import TeleClientSingleton
from TeleBotSingleton import TeleBotSingleton
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    InviteToChannelRequest,
    EditTitleRequest,
    EditBannedRequest,
    LeaveChannelRequest,
)
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.types import ChatBannedRights
from telethon import Button
from openai import AsyncOpenAI
from Config import Config
import json
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from common.constants import *
from client.client_calls.lang_dicts import *
from client.client_calls.functions import (
    now_iso,
    clear_session_data,
    initialize_user_session_data,
    session_data,
)
import common.lang_dicts
import logging
import utils.mobi_cash as mobi

log = logging.getLogger(__name__)

openai = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)


async def extract_text_from_photo(event, lang, payment_methods):
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
        log.info(f"النص المستخرج: {cleaned_text}")
        resp = await openai.chat.completions.create(
            model=Config.GPT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"You are a professional financial assistant.\n\n"
                        "Given the following payment or bank receipt text, analyze and extract all relevant fields.\n"
                        "Return your full response as a single JSON object with these fields:\n"
                        "- transaction_id (string)\n"
                        "- from (sender name, string)\n"
                        "- to (recipient name, string)\n"
                        "- amount (string/float)\n"
                        "- currency (string)\n"
                        f"- payment_method from our list of payment methods {payment_methods}\n"
                        "- date (in iso format)\n"
                        "- warnings (array of strings, if any field is suspicious or missing, else empty array)\n"
                        "- summary_ar (string, clear summary in Arabic)\n"
                        "- summary_en (string, clear summary in English)\n\n"
                        "If a field is missing, set its value to null.\n"
                        "If you detect other relevant info (such as extra logo, country, etc) add a field 'extra' as an object.\n\n"
                        "Output ONLY a valid JSON object, without any extra explanation or text.\n\n"
                        "Receipt OCR text:\n\n"
                        f"{cleaned_text}\n\n"
                        "Pre-parsed fields (for reference, use or correct them as needed):"
                    ),
                }
            ],
            temperature=0.7,
        )
        content = resp.choices[0].message.content.strip()
        if "```json" in content:
            json_part = content.split("```json")[1].split("```")[0].strip()
        parsed_details = json.loads(r"{}".format(json_part))
        return cleaned_text, parsed_details

    except Exception as e:
        log.error(f"خطأ في OCR (Google Vision): {e}")
        await event.reply(TEXTS[lang]["google_vision_error"])
        return None, None

    finally:
        if path and os.path.exists(path):
            os.remove(path)


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


async def start_session(uid: int, cid: int, st: str):
    tg_user = await TeleClientSingleton().get_entity(uid)
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
            s.commit()
        user_account = s.query(models.PlayerAccount).filter_by(user_id=uid).first()
        if not user_account:
            try:
                await TeleClientSingleton().send_message(
                    entity=user.user_id,
                    message=common.lang_dicts.TEXTS[user.lang][
                        "create_account_group_reply"
                    ].format(
                        user.name,
                        CREATE_ACCOUNT_LINKS[cid]["wlcm"].format(
                            user.user_id, user.user_id
                        ),
                        CREATE_ACCOUNT_LINKS[cid]["apk"].format(
                            user.user_id, user.user_id
                        ),
                        CREATE_ACCOUNT_LINKS[cid]["reg"].format(
                            user.user_id, user.user_id
                        ),
                    ),
                    link_preview=False,
                    parse_mode="html",
                )
            except Exception as e:
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=common.lang_dicts.TEXTS[user.lang]["start_chat_first"],
                )
                return
            await TeleClientSingleton().send_message(
                entity=cid,
                message=(
                    "You don't have an account with us yet ❗️\n\n"
                    + common.lang_dicts.TEXTS[user.lang]["link_sent_in_private"]
                ),
            )
            return
        try:
            is_user_blacklisted = s.get(models.Blacklist, uid)
            if is_user_blacklisted:
                await TeleClientSingleton().send_message(
                    entity=uid,
                    message=TEXTS[user.lang]["blacklisted_user"],
                )
                return
            gid, is_new = await get_or_create_session(uid, st, s)
            peer = await TeleClientSingleton().get_entity(gid)
            default_prompt = s.get(models.Setting, "gpt_prompt")
            session_prompt = s.get(models.Setting, f"gpt_prompt_{st}")
            if is_new:
                resp = await openai.chat.completions.create(
                    model=Config.GPT_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                session_prompt.value
                                if session_prompt
                                else default_prompt.value
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"A {st} session is opened with user {user.name}, welcome him.",
                        },
                    ],
                    temperature=0.7,
                )
                welcome = resp.choices[0].message.content.strip()
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
            if uid not in session_data or st not in session_data[uid]:
                initialize_user_session_data(user_id=uid, st=st)
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


async def auto_deposit(user: models.User, s: Session):
    st = "deposit"
    data = session_data[user.id][st]["data"]
    payment_method = (
        s.query(models.PaymentMethod).filter_by(name=data["payment_method"]).first()
    )
    transaction = add_transaction(
        data=data, user_id=user.id, st=st, payment_method_id=payment_method.id, s=s
    )
    if payment_method.mode == "auto":
        # TODO auto check if deposit arrived
        res = mobi.deposit(
            user_id=user.player_account.account_number, amount=data["amount"]
        )
        if res["Success"]:
            await TeleBotSingleton().send_message(
                entity=Config.ADMIN_ID,
                message=str(transaction),
                parse_mode="html",
            )
            return transaction.id
        return res["Message"]
    elif payment_method.name.lower() in ["e & money", "paydu", "payby"]:
        receipt = s.query(models.Receipt).filter_by(id=transaction.receipt_id).first()
        if receipt and not receipt.user_id:
            receipt.user_id = user.user_id
            s.commit()
            await TeleBotSingleton().send_message(
                entity=Config.ADMIN_ID,
                message=str(transaction),
                parse_mode="html",
            )
            return transaction.id
        return "Duplicate Receipt Id"
    else:
        await TeleBotSingleton().send_message(
            entity=Config.ADMIN_ID,
            message=str(transaction),
            parse_mode="html",
            buttons=(
                [
                    [
                        Button.inline(
                            text="موافقة ✅",
                            data=f"approve_{st}_{transaction.id}",
                        ),
                        Button.inline(
                            text="رفض ❌",
                            data=f"decline_{st}_{transaction.id}",
                        ),
                    ]
                ]
            ),
        )
        return transaction.id


async def auto_withdraw(user: models.User, s: Session):
    st = "withdraw"
    data = session_data[user.id][st]["data"]
    payment_method = (
        s.query(models.PaymentMethod).filter_by(name=data["payment_method"]).first()
    )
    transaction = add_transaction(
        data=data, user_id=user.id, st=st, payment_method_id=payment_method.id, s=s
    )
    res = mobi.withdraw(
        user_id=user.player_account.account_number,
        code=data["withdrawal_code"],
    )
    if res["Success"]:
        await TeleBotSingleton().send_message(
            entity=Config.ADMIN_ID,
            message=str(transaction),
            parse_mode="html",
            buttons=(
                [
                    [
                        Button.inline(
                            text="موافقة ✅",
                            data=f"approve_{st}_{transaction.id}",
                        ),
                        Button.inline(
                            text="رفض ❌",
                            data=f"decline_{st}_{transaction.id}",
                        ),
                    ]
                ]
            ),
        )
        return transaction.id
    return res["Message"]


def add_transaction(
    data: dict, user_id: int, st: str, payment_method_id: int, s: Session
):
    player_account = s.query(models.PlayerAccount).filter_by(user_id=user_id).first()
    if st == "deposit":
        transaction = models.Transaction(
            user_id=user_id,
            payment_method_id=payment_method_id,
            type=st,
            amount=data["amount"],
            currency=data["currency"],
            receipt_id=data["transaction_id"],
            player_account=player_account.account_number,
            status="pending",
            date=datetime.fromisoformat(data["date"]) if data["date"] else None,
            timestamp=now_iso(),
        )
    else:
        transaction = models.Transaction(
            user_id=user_id,
            payment_method_id=payment_method_id,
            type=st,
            withdrawal_code=data["withdrawal_code"],
            payment_info=data["payment_info"],
            player_account=player_account.account_number,
            status="pending",
            timestamp=now_iso(),
        )

    s.add(transaction)
    s.commit()
    return transaction


async def handle_fraud(
    uid: int,
    cid: int,
    st: str,
    user: models.User,
    duplicate: models.Receipt,
    extracted: str,
    transaction_id: int,
    s: Session,
):
    from_user = s.get(models.User, duplicate.user_id)
    s.add(
        models.FraudLog(
            user_id=uid,
            copied_from_id=duplicate.user_id,
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
                timestamp=now_iso(),
            )
        )
        s.commit()
        user_msg = (
            "Fraud attempt detected.\n"
            f"This transaction (ID: {transaction_id}) was sent by another user.\n"
            f"This is your attempt number {count}.\n"
            "You have been added to the blacklist."
        )
        admin_msg = (
            f"المستخدم @{user.username} (<code>{uid}</code>) في القائمة السوداء عدد المحاولات {count} ⚠️\n"
            f"رقم العملية الذي تمت المحاولة فيه: <code>{transaction_id}</code>\n"
            f"عائد للمستخدم @{from_user.username} (<code>{duplicate.user_id}</code>)"
        )
    else:
        user_msg = (
            "Fraud attempt detected.\n"
            f"This transaction (ID: {transaction_id}) was sent by another user.\n"
            f"This is your attempt number {count}.\n"
            "Note that if you reach 5 attempts, you will be blacklisted."
        )
        admin_msg = (
            f"محاولة احتيال رقم {count} للمستخدم @{user.username} (<code>{uid}</code>) ⚠️\n"
            f"رقم العملية الذي تمت المحاولة فيه: <code>{transaction_id}</code>\n"
            f"عائد للمستخدم @{from_user.username} (<code>{duplicate.user_id}</code>)"
        )
    await TeleClientSingleton().send_message(entity=cid, message=user_msg)
    await TeleClientSingleton().send_message(entity=Config.ADMIN_ID, message=admin_msg)
    if count >= 5:
        await kick_user_and_admin(gid=cid, uid=uid)
        clear_session_data(user_id=uid, st=st)

