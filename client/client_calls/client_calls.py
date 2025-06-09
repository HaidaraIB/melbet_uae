from client.client_calls.common import (
    start_session,
    extract_text_from_photo,
    kick_user_and_admin,
    submit_to_admin,
    handle_fraud,
    save_payment_text,
    openai,
    session_data,
)
from client.client_calls.functions import (
    save_session_data,
    initialize_user_session_data,
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
            user_account = s.query(models.MelbetAccount).filter_by(user_id=uid).first()
            if not user_account:
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=TEXTS[user.lang]["no_account"],
                )
                return
            st = user_session.session_type
            if uid not in session_data:
                initialize_user_session_data(user_id=uid, session_type=st)
            elif session_data[uid]["state"] != SessionState.AWAITING_RECEIPT.name:
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=f"A receipt was previously sent by you now we are {session_data[uid]['state']}",
                )
                return

            extracted, parsed_details = await extract_text_from_photo(
                event=event,
                lang=user.lang,
                payment_methods=list(
                    map(
                        str,
                        s.query(models.PaymentMethod)
                        .filter(models.PaymentMethod.type == st)
                        .all(),
                    )
                ),
            )
            if extracted:
                if not (parsed_details["amount"] and parsed_details["transaction_id"]):
                    missing = []
                    for k in session_data[uid]["metadata"]["required_fields"]:
                        if not parsed_details[k]:
                            missing.append(k)
                        else:
                            session_data[uid]["data"][k] = parsed_details[k]
                    details_str = "".join(
                        [f"{k}: {v}\n" for k, v in parsed_details.items() if v]
                    )
                    msg = (
                        f"text extracted from photo:\n"
                        f"{details_str}"
                        f"but we have a missing details: {missing}.\n"
                        "please provide them manually"
                    )
                    await TeleClientSingleton().send_message(
                        entity=cid,
                        message=msg,
                    )
                    session_data[uid][
                        "state"
                    ] = SessionState.AWAITING_MISSING_FIELDS.name
                    save_session_data()
                else:
                    transaction_id = parsed_details["transaction_id"]
                    for f in session_data[uid]["metadata"]["required_fields"]:
                        session_data[uid]["data"][f] = parsed_details[f]

                    if "date" not in parsed_details:
                        log.info(f"تفاصيل اختيارية مفقودة: ['date']")
                    else:
                        session_data[uid]["data"]["date"] = parsed_details["date"]

                    duplicate = (
                        s.query(models.PaymentText)
                        .filter(models.PaymentText.transaction_id == transaction_id)
                        .first()
                    )
                    if duplicate and duplicate.user_id != uid:
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
                    elif not duplicate:
                        await save_payment_text(
                            uid=uid,
                            cid=cid,
                            st=st,
                            extracted=extracted,
                            parsed_details=parsed_details,
                            transaction_id=transaction_id,
                            s=s,
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
            user_account = s.query(models.MelbetAccount).filter_by(user_id=uid).first()
            if not user_account:
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=TEXTS[user.lang]["no_account"],
                )
                return
            st = user_session.session_type
            session_prompt = s.get(models.Setting, f"gpt_prompt_{st}")
            if uid not in session_data:
                initialize_user_session_data(user_id=uid, session_type=st)
            payment_methods = list(
                map(
                    str,
                    s.query(models.PaymentMethod)
                    .filter(models.PaymentMethod.type == st)
                    .all(),
                )
            )
            txt: str = event.raw_text
            system_msg = (
                f"This message was sent by user {uid} in a {st} session\n"
                f"the state of the conversation is {session_data[uid]['state']} and the data we have are {session_data[uid]['data']}\n"
                f"the user just sent the msg {txt} if we're at AWAITING_MISSING_FIELDS state and the msg contains one of the missing fields please extract it and respond with only a json like the data I previously provided\n"
                f"the payment methods we have in case the user msg contained one: {payment_methods}\n"
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
                details_str = "".join(
                    [
                        f"{k}: {v}\n"
                        for k, v in parsed_details.items()
                        if v and not session_data[uid]["data"][k]
                    ]
                )
                for d in parsed_details:
                    session_data[uid]["data"][d] = parsed_details[d]
                user_msg = f"missing info recieved:\n{details_str}"
                data_complete = True
                for k, v in session_data[uid]["data"].items():
                    if k in session_data[uid]["metadata"]["required_fields"] and not v:
                        data_complete = False
                if data_complete:
                    completed_data = "".join(
                        [
                            f"{k}: {v}\n"
                            for k, v in session_data[uid]["data"].items()
                            if v
                        ]
                    )
                    user_msg += (
                        "Required data completed:\n"
                        f"{completed_data}\n"
                        "you can send OK if all the information are correct."
                    )
                    session_data[uid]["state"] = SessionState.AWAITING_CONFIRMATION.name
            except json.decoder.JSONDecodeError:
                user_msg = reply
            await TeleClientSingleton().send_message(entity=cid, message=user_msg)
    save_session_data()
    raise events.StopPropagation


async def send_transaction_to_proccess(event: events.NewMessage.Event):
    uid = event.sender_id
    if (
        not event.is_group
        or not event.raw_text
        or session_data[uid]["state"] != SessionState.AWAITING_CONFIRMATION.name
    ):
        return
    cid = event.chat_id
    ent = await TeleClientSingleton().get_entity(cid)
    with models.session_scope() as s:
        user_session = s.query(models.UserSession).filter_by(group_id=ent.id).first()
        user = s.get(models.User, uid)
        if user_session and uid == user_session.user_id:
            user_account = s.query(models.MelbetAccount).filter_by(user_id=uid).first()
            if not user_account:
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=TEXTS[user.lang]["no_account"],
                )
                return
            await submit_to_admin(user=user, s=s)
            await kick_user_and_admin(
                gid=user_session.group_id, uid=user_session.user_id
            )
    clear_session_data(user_id=uid)
    raise events.StopPropagation


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
            await kick_user_and_admin(
                gid=user_session.group_id, uid=user_session.user_id
            )
            clear_session_data(user_id=user_session.user_id)
    raise events.StopPropagation
