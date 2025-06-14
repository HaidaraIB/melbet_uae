from client.client_calls.common import (
    start_session,
    extract_text_from_photo,
    kick_user_and_admin,
    handle_fraud,
    auto_withdraw,
    auto_deposit,
    openai,
    session_data,
)
from client.client_calls.functions import (
    save_session_data,
    classify_intent,
    clear_session_data,
)
from client.client_calls.constants import SessionState
from client.client_calls.lang_dicts import *
from TeleClientSingleton import TeleClientSingleton
from telethon import events
from Config import Config
import models
import json
import logging

log = logging.getLogger(__name__)


async def get_receipt(event: events.NewMessage.Event):
    if not event.is_group or not event.photo:
        return
    cid = event.chat_id
    uid = event.sender_id
    ent = await TeleClientSingleton().get_entity(cid)
    with models.session_scope() as s:
        user_session = s.query(models.UserSession).filter_by(group_id=ent.id).first()
        user = s.get(models.User, uid)
        if user_session and uid == user_session.user_id:
            user_account = s.query(models.PlayerAccount).filter_by(user_id=uid).first()
            if not user_account:
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=TEXTS[user.lang]["no_account"],
                )
                return
            st = user_session.session_type
            if st != "deposit":
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=f"Receipts can only be send in deposit sessions, withdraw info must be provided manualy.",
                )
                return

            extracted, parsed_details = await extract_text_from_photo(
                event=event,
                lang=user.lang,
                payment_methods=list(
                    map(
                        str,
                        s.query(models.PaymentMethod)
                        .filter(models.PaymentMethod.type.in_([st, "both"]))
                        .all(),
                    )
                ),
            )
            if extracted:
                if parsed_details["transaction_id"]:
                    transaction_id = parsed_details["transaction_id"]
                    duplicate = (
                        s.query(models.Receipt)
                        .filter(models.Receipt.id == transaction_id)
                        .first()
                    )
                    if duplicate and duplicate.user_id is not None and duplicate.user_id != uid:
                        await handle_fraud(
                            uid=uid,
                            cid=cid,
                            st=st,
                            user=user,
                            duplicate=duplicate,
                            extracted=extracted,
                            transaction_id=transaction_id,
                            s=s,
                        )
                        return
                details_str = "".join(
                    [
                        f"{k}: {v}\n"
                        for k, v in parsed_details.items()
                        if v and k in session_data[uid][st]["data"]
                    ]
                )
                if not all(
                    parsed_details[f]
                    for f in session_data[uid]["metadata"]["required_deposit_fields"]
                ):
                    missing = []
                    for k in session_data[uid]["metadata"]["required_deposit_fields"]:
                        if not parsed_details[k]:
                            missing.append(k)
                        else:
                            session_data[uid][st]["data"][k] = parsed_details[k]
                    msg = (
                        f"text extracted from photo:\n\n"
                        f"<code>{details_str}</code>\n"
                        f"but we have a missing details: ({', '.join(missing)}). Please provide them manually"
                    )
                else:
                    for f in session_data[uid]["metadata"]["required_deposit_fields"]:
                        session_data[uid][st]["data"][f] = parsed_details[f]
                    msg = (
                        f"Receipt verified successfully, required fields extracted:\n\n"
                        f"<code>{details_str}</code>\n\n"
                    )
                    msg += "You can send OK if all the information are correct."
                if "date" not in parsed_details:
                    log.info(f"تفاصيل اختيارية مفقودة: ['date']")
                    msg += "optional fields (date) are missing, please provide them manually if they're present."
                else:
                    session_data[uid][st]["data"]["date"] = parsed_details["date"]
                await TeleClientSingleton().send_message(
                    entity=cid, message=msg, parse_mode="html"
                )

            save_session_data()
    raise events.StopPropagation


async def get_missing(event: events.NewMessage.Event):
    if not event.is_group or event.photo:
        return
    cid = event.chat_id
    uid = event.sender_id
    ent = await TeleClientSingleton().get_entity(cid)
    with models.session_scope() as s:
        default_prompt = s.get(models.Setting, "gpt_prompt")
        user_session = s.query(models.UserSession).filter_by(group_id=ent.id).first()
        user = s.get(models.User, uid)
        if user_session and uid == user_session.user_id:
            user_account = s.query(models.PlayerAccount).filter_by(user_id=uid).first()
            if not user_account:
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=TEXTS[user.lang]["no_account"],
                )
                return
            st = user_session.session_type
            session_prompt = s.get(models.Setting, f"gpt_prompt_{st}")
            payment_methods = list(
                map(
                    str,
                    s.query(models.PaymentMethod)
                    .filter(models.PaymentMethod.type.in_([st, "both"]))
                    .all(),
                )
            )
            txt: str = event.raw_text
            system_msg = (
                f"This message was sent by user {uid} in a {st} session\n"
                f"the state of the conversation is {session_data[uid][st]['state']} and the data we have is {session_data[uid][st]['data']}\n"
                f"the user just sent the msg '{txt}' if we're at AWAITING_MISSING_FIELDS state and the msg contains one of the missing fields please extract it and respond only with it in a JSON like the data I previously provided\n"
                f"the payment methods we have in case the user msg contained one: {payment_methods}\n"
                "Important Notes:"
                "- Don't use single quotes\n"
                "- Dates in ISO format\n"
                "- Withdrawal codes are mix of numbers and letters with no meaning whatsoever\n"
                "- Payment info is like a bank account number, a wallet address, an IBAN number or something similar\n"
                "if the msg was a question or something other than a data just respond to it in its language as the following\n"
                f"{session_prompt.value if session_prompt else default_prompt.value}"
            )
            resp = await openai.chat.completions.create(
                model=Config.GPT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_msg,
                    },
                    {
                        "role": "user",
                        "content": txt,
                    },
                ],
                temperature=0.7,
            )
            reply = resp.choices[0].message.content.strip()
            try:
                if "```json" in reply:
                    reply = reply.split("```json")[1].split("```")[0].strip()
                parsed_details: dict = json.loads(r"{}".format(reply))
                for d in parsed_details:
                    session_data[uid][st]["data"][d] = parsed_details[d]
                provided_data = "".join(
                    [f"{k}: {v}\n" for k, v in parsed_details.items() if v]
                )
                user_msg = (
                    f"missing/edited info recieved:\n\n"
                    f"<code>{provided_data}</code>\n"
                )
                if parsed_details.get("transaction_id", None):
                    transaction_id = parsed_details["transaction_id"]
                    duplicate = (
                        s.query(models.Receipt)
                        .filter(models.Receipt.id == transaction_id)
                        .first()
                    )
                    if duplicate and duplicate.user_id is not None and duplicate.user_id != uid:
                        await handle_fraud(
                            uid=uid,
                            cid=cid,
                            st=st,
                            user=user,
                            duplicate=duplicate,
                            extracted=reply,
                            transaction_id=transaction_id,
                            s=s,
                        )
                        return
                if all(
                    session_data[uid][st]["data"][f]
                    for f in session_data[uid]["metadata"][f"required_{st}_fields"]
                ):
                    completed_data = "".join(
                        [
                            f"{k}: {v}\n"
                            for k, v in session_data[uid][st]["data"].items()
                            if v
                        ]
                    )
                    user_msg += (
                        "Required data completed:\n\n"
                        f"<code>{completed_data}</code>\n"
                        "you can send OK if all the information are correct.\n\n"
                        "Note that withdrawal take <b>from 1 up to 24 hours</b> to complete"
                    )
                    session_data[uid][st][
                        "state"
                    ] = SessionState.AWAITING_CONFIRMATION.name
                else:
                    missing_data = "".join(
                        [
                            f"{k}: {v}\n"
                            for k, v in session_data[uid][st]["data"].items()
                            if not v
                        ]
                    )
                    user_msg += (
                        "Required fields not yet provided:\n\n"
                        f"<code>{missing_data}</code>\n"
                        "Please provide them manualy."
                    )

            except json.decoder.JSONDecodeError:
                user_msg = reply
            await TeleClientSingleton().send_message(
                entity=cid,
                message=user_msg,
                parse_mode="html",
            )
            save_session_data()
    raise events.StopPropagation


async def send_transaction_to_proccess(event: events.NewMessage.Event):
    uid = event.sender_id
    if not event.is_group or not event.raw_text:
        return
    cid = event.chat_id
    ent = await TeleClientSingleton().get_entity(cid)
    with models.session_scope() as s:
        user_session = s.query(models.UserSession).filter_by(group_id=ent.id).first()
        user = s.get(models.User, uid)
        if user_session and uid == user_session.user_id:
            user_account = s.query(models.PlayerAccount).filter_by(user_id=uid).first()
            st = user_session.session_type
            if (
                session_data[uid][st]["state"]
                != SessionState.AWAITING_CONFIRMATION.name
            ):
                return
            if not user_account:
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=TEXTS[user.lang]["no_account"],
                )
                return
            if st == "withdraw":
                res = await auto_withdraw(user=user, s=s)
            else:
                res = await auto_deposit(user=user, s=s)
            if not isinstance(res, int):
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=TEXTS[user.lang][f"{st}_failed"].format(res),
                )
                return
            await kick_user_and_admin(
                gid=user_session.group_id, uid=user_session.user_id
            )
            await TeleClientSingleton().send_message(
                entity=uid,
                message=(
                    f"Alright we're processing your transaction number <code>{res}</code>, and we'll catch up with you soon\n\n"
                    "Note that withdrawal take <b>from 1 up to 24 hours</b> to complete"
                ),
                parse_mode="html",
            )
            clear_session_data(user_id=uid, st=st)
    raise events.StopPropagation


async def listen_to_dp_and_wd_requests(event: events.NewMessage.Event):
    uid = event.sender_id
    cid = event.chat_id
    sender = await TeleClientSingleton().get_permissions(entity=cid, user=uid)
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
            user = s.get(models.User, uid)
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
                                + f"User {user.name} wants to {intent}",
                            },
                        ],
                        temperature=0.3,
                    )
                )
                .choices[0]
                .message.content.strip()
            )
            await TeleClientSingleton().send_message(entity=cid, message=note)
    except Exception as e:
        log.error(f"خطأ في إنشاء إشعار OpenAI: {e}")
    await start_session(uid=uid, cid=cid, st=intent)
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
            resp = await openai.chat.completions.create(
                model=Config.GPT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            manager_prompt.value
                            if manager_prompt
                            else default_prompt.value
                        ),
                    },
                    {
                        "role": "user",
                        "content": txt,
                    },
                ],
                temperature=0.7,
            )
            reply = resp.choices[0].message.content.strip()
            await TeleClientSingleton().send_message(uid, reply)
        except Exception as e:
            log.error(f"Error while generally responding to user {uid}: {e}")
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
            st = user_session.session_type
            await kick_user_and_admin(
                gid=user_session.group_id, uid=user_session.user_id
            )
            clear_session_data(user_id=user_session.user_id, st=st)
    raise events.StopPropagation
