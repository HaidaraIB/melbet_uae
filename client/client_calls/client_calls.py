from client.client_calls.common import (
    start_session,
    extract_text_from_photo,
    kick_user_and_admin,
    handle_fraud,
    process_withdraw,
    process_deposit,
    auto_deposit,
    send_and_pin_payment_methods_keyboard,
    send_and_pin_player_accounts_keyboard,
    generate_stripe_payment_link,
    session_data,
)
from client.client_calls.functions import (
    save_session_data,
    classify_intent,
    clear_session_data,
    check_stripe_payment_webhook,
)
from client.client_calls.constants import *
from client.client_calls.lang_dicts import *
from TeleClientSingleton import TeleClientSingleton
from TeleBotSingleton import TeleBotSingleton
from telethon import events, Button
from sqlalchemy import and_
from Config import Config
import models
import json
import asyncio
import stripe
import logging

log = logging.getLogger(__name__)


async def choose_account_number(event: events.CallbackQuery.Event):
    if not event.is_group:
        return
    cid = event.chat_id
    uid = event.sender_id
    group = await TeleBotSingleton().get_entity(entity=cid)
    with models.session_scope() as s:
        user_session = s.query(models.UserSession).filter_by(group_id=group.id).first()
        if user_session and uid == user_session.user_id:
            account_number = event.data.decode("utf-8").split("_")[-1]
            session_data[uid]["metadata"]["account_number"] = account_number
            await event.answer(
                message=TEXTS[user_session.user.lang]["player_account_set"],
                alert=True,
            )
            save_session_data()
    raise events.StopPropagation


async def choose_payment_method(event: events.CallbackQuery.Event):
    if not event.is_group:
        return
    cid = event.chat_id
    uid = event.sender_id
    group = await TeleBotSingleton().get_entity(entity=cid)
    with models.session_scope() as s:
        user_session = s.query(models.UserSession).filter_by(group_id=group.id).first()
        st = user_session.session_type
        if user_session and uid == user_session.user_id:
            account_number = session_data[uid]["metadata"]["account_number"]
            if not account_number:
                await event.answer(
                    message=TEXTS[user_session.user.lang]["choose_account_first"],
                    alert=True,
                )
                return
            player_account = (
                s.query(models.PlayerAccount)
                .filter_by(account_number=account_number)
                .first()
            )
            payment_method_id = int(event.data.decode("utf-8").split("_")[-1])
            payment_method = (
                s.query(models.PaymentMethod).filter_by(id=payment_method_id).first()
            )
            if player_account.country != payment_method.country:
                await event.answer(
                    message=TEXTS[user_session.user.lang][
                        "incompatible_payment_method"
                    ],
                    alert=True,
                )
                return
            session_data[uid]["metadata"]["payment_method"] = payment_method_id
            await event.answer(
                message=TEXTS[user_session.user.lang]["payment_method_set"], alert=True
            )
            if st == "deposit":
                if payment_method.mode == "stripe":
                    stripe_link = generate_stripe_payment_link(uid=uid)
                    session_data[uid]["metadata"]["stripe_link"] = stripe_link
                    await TeleBotSingleton().send_message(
                        entity=group.id,
                        message=TEXTS[user_session.user.lang]["stripe_payment_text"],
                        buttons=[
                            [
                                Button.url(
                                    text=BUTTONS[user_session.user.lang]["link"],
                                    url=stripe_link["url"],
                                )
                            ],
                            [
                                Button.inline(
                                    text=BUTTONS[user_session.user.lang]["done"],
                                    data="payment_done",
                                )
                            ],
                        ],
                        parse_mode="html",
                    )
                    session_data[uid][st]["state"] = SessionState.AWAITING_PAYMENT.name
                else:
                    await TeleBotSingleton().send_message(
                        entity=group.id,
                        message=TEXTS[user_session.user.lang][
                            "payemnt_method_info"
                        ].format(payment_method.name, payment_method.details),
                        parse_mode="html",
                    )
                    session_data[uid][st]["state"] = SessionState.AWAITING_RECEIPT.name
            else:
                await TeleBotSingleton().send_message(
                    entity=group.id,
                    message=TEXTS[user_session.user.lang]["provide_withdrawal_info"],
                    parse_mode="html",
                )
                session_data[uid][st][
                    "state"
                ] = SessionState.AWAITING_MISSING_FIELDS.name
            save_session_data()
    raise events.StopPropagation


async def check_payment(event: events.CallbackQuery.Event):
    if not event.is_group:
        return
    cid = event.chat_id
    uid = event.sender_id
    group = await TeleBotSingleton().get_entity(entity=cid)
    with models.session_scope() as s:
        user = s.get(models.User, uid)
        user_session = s.query(models.UserSession).filter_by(group_id=group.id).first()
        if user_session and uid == user_session.user_id:
            if (
                session_data[uid]["deposit"]["state"]
                != SessionState.AWAITING_PAYMENT.name
            ):
                await event.answer(
                    message=TEXTS[user.lang]["not_at_this_state_yet"], alert=True
                )
                return
            if not session_data[uid]["metadata"]["account_number"]:
                await send_and_pin_player_accounts_keyboard(
                    group=cid,
                    player_accounts=s.query(models.PlayerAccount)
                    .filter_by(user_id=uid)
                    .all(),
                    st="deposit",
                )
                return
            stripe_link = session_data[uid]["metadata"]["stripe_link"]
            data = await check_stripe_payment_webhook(uid=uid)
            if data:
                res = await auto_deposit(data=data, user=user, s=s)
                stripe.PaymentLink.modify(id=stripe_link["id"], active=False)
                if not isinstance(res, int):
                    await TeleClientSingleton().send_message(
                        entity=cid,
                        message=TEXTS[user.lang][f"deposit_failed"].format(res),
                    )
                    return
                await event.edit(TEXTS[user.lang]["successful_deposit_closing_in_5"])
                await asyncio.sleep(5)
                await kick_user_and_admin(gid=user_session.group_id, uid=uid)
                clear_session_data(user_id=uid)
            else:
                await TeleBotSingleton().send_message(
                    entity=user_session.group_id,
                    message=TEXTS[user.lang]["payment_not_successful"],
                )
    raise events.StopPropagation


async def get_receipt(event: events.NewMessage.Event):
    if not event.is_group or not event.photo:
        return
    cid = event.chat_id
    uid = event.sender_id
    group = await TeleClientSingleton().get_entity(entity=cid)
    with models.session_scope() as s:
        user_session = s.query(models.UserSession).filter_by(group_id=group.id).first()
        user = s.get(models.User, uid)
        if user_session and uid == user_session.user_id:
            st = user_session.session_type
            if st != "deposit":
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=TEXTS[user.lang]["receipt_in_withdraw_session"],
                )
                return
            elif session_data[uid][st]["state"] not in [
                SessionState.AWAITING_RECEIPT.name,
                SessionState.AWAITING_MISSING_FIELDS.name,
            ]:
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=TEXTS[user.lang]["select_payment_method_first"],
                )
                return
            extracted, parsed_details = await extract_text_from_photo(
                event=event,
                lang=user.lang,
                payment_methods=list(
                    map(
                        str,
                        s.query(models.PaymentMethod)
                        .filter(
                            and_(
                                models.PaymentMethod.type.in_([st, "both"]),
                                models.PaymentMethod.is_active == True,
                                (
                                    models.PaymentMethod.country
                                    == (
                                        "uae"
                                        if user.from_group_id
                                        == Config.UAE_MONITOR_GROUP_ID
                                        else "syr"
                                    )
                                ),
                            )
                        )
                        .all(),
                    )
                ),
            )
            if extracted:
                if parsed_details["receipt_id"]:
                    receipt_id = parsed_details["receipt_id"]
                    duplicate = (
                        s.query(models.Receipt)
                        .filter(models.Receipt.id == receipt_id)
                        .first()
                    )
                    if duplicate and duplicate.transaction_id:
                        await handle_fraud(
                            uid=uid,
                            cid=cid,
                            user=user,
                            duplicate=duplicate,
                            extracted=extracted,
                            transaction_id=receipt_id,
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

                if "date" not in parsed_details:
                    log.info(f"تفاصيل اختيارية مفقودة: ['date']")
                    msg += TEXTS[user.lang]["optional_missing"]
                else:
                    session_data[uid][st]["data"]["date"] = parsed_details["date"]

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
                    msg = TEXTS[user.lang]["text_extracted_from_photo"].format(
                        details_str, ", ".join(missing)
                    )
                    await TeleClientSingleton().send_message(
                        entity=cid, message=msg, parse_mode="html"
                    )
                    session_data[uid][st][
                        "state"
                    ] = SessionState.AWAITING_MISSING_FIELDS.name
                else:
                    for f in session_data[uid]["metadata"]["required_deposit_fields"]:
                        session_data[uid][st]["data"][f] = parsed_details[f]
                    msg = TEXTS[user.lang]["receipt_verified_success"].format(
                        details_str
                    )
                    await TeleBotSingleton().send_message(
                        entity=cid,
                        message=msg,
                        parse_mode="html",
                        buttons=Button.inline(
                            text="OK", data="send_transaction_to_proccess"
                        ),
                    )
                    session_data[uid][st][
                        "state"
                    ] = SessionState.AWAITING_CONFIRMATION.name

            save_session_data()
    raise events.StopPropagation


async def get_missing(event: events.NewMessage.Event):
    if not event.is_group or event.photo:
        return
    cid = event.chat_id
    uid = event.sender_id
    group = await TeleClientSingleton().get_entity(entity=cid)
    with models.session_scope() as s:
        user_session = s.query(models.UserSession).filter_by(group_id=group.id).first()
        user = s.get(models.User, uid)
        if user_session and uid == user_session.user_id:
            st = user_session.session_type
            txt: str = event.raw_text
            default_prompt = s.get(models.Setting, "gpt_prompt")
            session_prompt = s.get(models.Setting, f"gpt_prompt_{st}")
            if session_data[uid][st]["state"] in [
                SessionState.AWAITING_PAYMENT.name,
                SessionState.AWAITING_PAYMENT_METHOD.name,
            ]:
                system_msg = (
                    f"User {uid} in state {session_data[uid][st]['state']}.\n"
                    "Handle ONLY as follows:\n"
                    "- If awaiting payment confirmation (AWAITING_PAYMENT), respond only: 'display_done_button'.\n"
                    "- If awaiting payment method or user asks payment-related question, respond only: 'display_payment_methods_keyboard'.\n"
                    "- Otherwise, respond briefly and humanly in user's language:\n"
                    f"{session_prompt.value if session_prompt else default_prompt.value}\n"
                    "Keep response concise, natural, and human-like."
                )
            else:
                system_msg = (
                    f"User {uid}, session: {st}, state: {session_data[uid][st]['state']}.\n"
                    f"Collected data: {session_data[uid][st]['data']}.\n"
                    f"User message: '{txt}'.\n"
                    "Instructions:\n"
                    "- If at AWAITING_MISSING_FIELDS and missing data provided, respond ONLY with provided data in strict JSON format:\n"
                    "  * No single quotes\n"
                    "  * Dates ISO format\n"
                    "  * Withdrawal codes random alphanumeric\n"
                    "  * Payment info examples: bank accounts, wallet addresses, IBAN\n"
                    "- If user asks payment methods, respond only: 'display_payment_methods_keyboard'.\n"
                    "- If at AWAITING_CONFIRMATION and user asks next step, respond only: 'display_ok_button'.\n"
                    "- Otherwise, respond briefly, conversationally, and naturally:\n"
                    f"{session_prompt.value if session_prompt else default_prompt.value}\n"
                    "Keep response concise, natural, and human-like."
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
                user_msg = TEXTS[user.lang]["missing_info_received"].format(
                    provided_data
                )
                if parsed_details.get("receipt_id", None):
                    receipt_id = parsed_details["receipt_id"]
                    duplicate = (
                        s.query(models.Receipt)
                        .filter(models.Receipt.id == receipt_id)
                        .first()
                    )
                    if duplicate and duplicate.transaction_id:
                        await handle_fraud(
                            uid=uid,
                            cid=cid,
                            user=user,
                            duplicate=duplicate,
                            extracted=reply,
                            transaction_id=receipt_id,
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
                    user_msg += TEXTS[user.lang]["required_data_completed"].format(
                        completed_data
                    )
                    if st == "withdraw":
                        user_msg += TEXTS[user.lang]["withdrawals_delay"]
                    await TeleBotSingleton().send_message(
                        entity=cid,
                        message=user_msg,
                        parse_mode="html",
                        buttons=Button.inline(
                            text="OK", data="send_transaction_to_proccess"
                        ),
                    )
                    session_data[uid][st][
                        "state"
                    ] = SessionState.AWAITING_CONFIRMATION.name
                else:
                    missing_data = "".join(
                        [
                            f"{k}: {v}\n"
                            for k, v in session_data[uid][st]["data"].items()
                            if (
                                not v
                                and k
                                in session_data[uid]["metadata"][
                                    "required_deposit_fields"
                                ]
                            )
                        ]
                    )
                    user_msg += TEXTS[user.lang]["missing_required"].format(
                        missing_data
                    )
                    await TeleClientSingleton().send_message(
                        entity=cid,
                        message=user_msg,
                        parse_mode="html",
                    )

            except json.decoder.JSONDecodeError:
                user = s.get(models.User, uid)
                if reply == "display_payment_methods_keyboard":
                    await send_and_pin_payment_methods_keyboard(
                        s=s, st=st, group=group.id, from_group_id=user.from_group_id
                    )
                    return
                elif reply == "display_done_button":
                    stripe_link = session_data[uid]["metadata"]["stripe_link"]
                    await TeleBotSingleton().send_message(
                        entity=group.id,
                        message=TEXTS[user_session.user.lang]["stripe_payment_text"],
                        buttons=[
                            [
                                Button.url(
                                    text=BUTTONS[user_session.user.lang]["link"],
                                    url=stripe_link["url"],
                                )
                            ],
                            [
                                Button.inline(
                                    text=BUTTONS[user_session.user.lang]["done"],
                                    data="payment_done",
                                )
                            ],
                        ],
                        parse_mode="html",
                    )
                    return
                elif reply == "display_ok_button":
                    completed_data = "".join(
                        [
                            f"{k}: {v}\n"
                            for k, v in session_data[uid][st]["data"].items()
                            if v
                        ]
                    )
                    user_msg = TEXTS[user.lang]["required_data_completed"].format(
                        completed_data
                    )
                    await TeleBotSingleton().send_message(
                        entity=cid,
                        message=user_msg,
                        parse_mode="html",
                        buttons=Button.inline(
                            text="OK", data="send_transaction_to_proccess"
                        ),
                    )
                    return
                user_msg = reply
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=user_msg,
                    parse_mode="html",
                )
            save_session_data()
    raise events.StopPropagation


async def send_transaction_to_proccess(event: events.CallbackQuery.Event):
    if not event.is_group:
        return
    uid = event.sender_id
    cid = event.chat_id
    ent = await TeleClientSingleton().get_entity(entity=cid)
    with models.session_scope() as s:
        user_session = s.query(models.UserSession).filter_by(group_id=ent.id).first()
        user = s.get(models.User, uid)
        if user_session and uid == user_session.user_id:
            st = user_session.session_type
            if (
                session_data[uid][st]["state"]
                != SessionState.AWAITING_CONFIRMATION.name
            ):
                await event.respond(TEXTS[user.lang]["not_at_this_state_yet"])
                return
            account_number = session_data[uid]["metadata"]["account_number"]
            if not account_number:
                await send_and_pin_player_accounts_keyboard(
                    group=cid,
                    player_accounts=s.query(models.PlayerAccount)
                    .filter_by(user_id=uid)
                    .all(),
                    st=st,
                )
                return
            player_account = (
                s.query(models.PlayerAccount)
                .filter_by(account_number=account_number)
                .first()
            )
            if (
                st == "deposit"
                and session_data[uid]["deposit"]["data"]["currency"].lower()
                != player_account.currency
            ):
                await event.respond(
                    TEXTS[user.lang]["mismatch_currency"].format(account_number)
                )
                return

            if st == "withdraw":
                res = await process_withdraw(user=user, s=s)
            else:
                res = await process_deposit(user=user, s=s)
            if not isinstance(res, int):
                await TeleClientSingleton().send_message(
                    entity=cid,
                    message=TEXTS[user.lang][f"{st}_failed"].format(res),
                )
                return
            await TeleClientSingleton().send_message(
                entity=cid,
                message=TEXTS[user.lang]["transaction_under_review_closing_in_5"],
            )
            await asyncio.sleep(5)
            await kick_user_and_admin(
                gid=user_session.group_id, uid=user_session.user_id
            )
            clear_session_data(user_id=uid)
    raise events.StopPropagation


async def listen_to_dp_and_wd_requests(event: events.NewMessage.Event):
    uid = event.sender_id
    cid = event.chat_id
    sender_permissions = await TeleClientSingleton().get_permissions(
        entity=cid, user=uid
    )
    if sender_permissions.is_admin:
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
            if not user:
                user = models.User(
                    user_id=uid,
                    username=event.sender.username or "N/A",
                    name=(event.sender.first_name or "")
                    + " "
                    + (event.sender.last_name or ""),
                    lang=(
                        models.Language.ARABIC
                        if cid == Config.SYR_MONITOR_GROUP_ID
                        else models.Language.ENGLISH
                    ),
                    from_group_id=cid,
                )
                s.add(user)
            elif not user.from_group_id:
                user.from_group_id = cid
            s.commit()
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
                                + f"\nsome user wants to {intent}",
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
            clear_session_data(user_id=user_session.user_id)
    raise events.StopPropagation
