from telegram import Update, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from Config import Config
from common.keyboards import build_back_button
import models
from client.client_calls.lang_dicts import *
from client.client_calls.custom_filters import DeclineReason, NewAmount, Proof
from client.client_calls.keyboards import (
    build_process_deposit_options_keyboard,
    build_process_transaction_keyboard,
)
from client.client_calls.common import now_iso
from user.buy_voucher.common import gift_voucher
from TeleClientSingleton import TeleClientSingleton
import utils.mobi_cash as mobi
import os


async def approve_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.effective_chat.type == Chat.PRIVATE
        and update.effective_user.id == Config.ADMIN_ID
    ):
        transaction_id = int(update.callback_query.data.split("_")[-1])
        transaction_type = update.callback_query.data.split("_")[-2]
        keyboard = [
            build_back_button(
                data=f"back_to_handle_{transaction_type}_{transaction_id}"
            ),
        ]
        if transaction_type == "deposit":
            keyboard.insert(
                0,
                build_process_deposit_options_keyboard(transaction_id=transaction_id),
            )
        else:
            await update.callback_query.answer(
                text="قم بالرد على هذه الرسالة بصورة لتأكيد العملية",
                show_alert=True,
            )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def confirm_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.effective_chat.type == Chat.PRIVATE
        and update.effective_user.id == Config.ADMIN_ID
    ):
        transaction_id = int(update.callback_query.data.split("_")[-1])
        with models.session_scope() as s:
            transaction = s.get(models.Transaction, transaction_id)
            if transaction.status == "approved":
                await update.callback_query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup.from_button(
                        InlineKeyboardButton(
                            text="تمت الموافقة ✅",
                            callback_data="✅✅✅",
                        )
                    )
                )
                return
            user = s.get(models.User, transaction.user_id)
            player_account = (
                s.query(models.PlayerAccount)
                .filter_by(account_number=transaction.account_number)
                .first()
            )
            res = await mobi.deposit(
                user_id=transaction.account_number,
                amount=transaction.amount,
                country=player_account.country,
            )
            if res["Success"]:
                transaction.status = "approved"
                transaction.mobi_operation_id = res["OperationId"]
                transaction.completed_at = now_iso()
                s.commit()
                message = TEXTS[user.lang]["deposit_approved"].format(
                    transaction.id,
                    transaction.amount,
                    transaction.currency,
                    transaction.player_account,
                )
                offer_progress = player_account.check_offer_progress(s=s)
                if offer_progress.get("completed", False):
                    player_account.offer_completed = True
                    offer_tx = models.Transaction.add_offer_transaction(
                        s=s, player_account=player_account
                    )
                    offer_dp = await mobi.deposit(
                        user_id=transaction.account_number,
                        amount=player_account.offer_prize,
                        country=player_account.country,
                    )
                    if offer_dp["Success"]:
                        offer_tx.status = "approved"
                        offer_tx.mobi_operation_id = res["OperationId"]
                        offer_tx.completed_at = now_iso()
                    else:
                        offer_tx.status = "failed"
                        offer_tx.fail_reason = res["Message"]
                    await TeleClientSingleton().send_message(
                        entity=user.user_id,
                        message=TEXTS[user.lang]["offer_completed_msg"],
                    )
                elif offer_progress.get("completed", None) is not None:
                    message += TEXTS[transaction.user.lang]["progress_msg"].format(
                        offer_progress["amount_left"],
                        player_account.currency,
                        offer_progress["deposit_days_left"],
                        player_account.offer_expiry_date,
                    )
                await TeleClientSingleton().send_message(
                    entity=transaction.user_id,
                    message=message,
                    parse_mode="html",
                )
                await update.callback_query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup.from_button(
                        InlineKeyboardButton(
                            text="تمت الموافقة ✅",
                            callback_data="✅✅✅",
                        )
                    )
                )
                s.commit()
            else:
                transaction.status = "failed"
                transaction.fail_reason = res["Message"]
                await update.callback_query.answer(
                    text=res["Message"],
                    show_alert=True,
                )
            if (player_account.currency == "aed" and transaction.amount >= 100) or (
                player_account.currency == "syr" and transaction.amount >= 100_000
            ):
                await gift_voucher(uid=user.user_id, s=s, lang=transaction.user.lang)


async def get_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.effective_chat.type == Chat.PRIVATE
        and update.effective_user.id == Config.ADMIN_ID
    ):
        transaction_id = int(
            update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.split("_")[-1]
        )

        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        with models.session_scope() as s:
            transaction = s.get(models.Transaction, transaction_id)
            transaction.status = "approved"
            transaction.completed_at = now_iso()
            new_proof = models.Proof(
                transaction_id=transaction.id,
                photo_data=bytes(photo_bytes),
            )
            s.add(new_proof)
            s.commit()
            user = s.get(models.User, transaction.user_id)
            photo_path = await photo_file.download_to_drive()
            await TeleClientSingleton().send_file(
                entity=transaction.user_id,
                file=photo_path,
                caption=TEXTS[user.lang]["withdraw_approved"].format(
                    transaction.id,
                    transaction.withdrawal_code,
                    transaction.player_account,
                ),
                parse_mode="html",
            )
            os.remove(photo_path)
            await update.message.reply_to_message.edit_reply_markup(
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(
                        text="تمت الموافقة ✅",
                        callback_data="✅✅✅",
                    )
                )
            )
            await update.message.reply_text(
                text="تمت الموافقة ✅",
                reply_to_message_id=update.message.reply_to_message.id,
            )


async def edit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.effective_chat.type == Chat.PRIVATE
        and update.effective_user.id == Config.ADMIN_ID
    ):
        transaction_id = int(update.callback_query.data.split("_")[-1])
        transaction_type = update.callback_query.data.split("_")[-2]
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بالمبلغ الجديد",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_row(
                build_back_button(
                    data=f"back_to_edit_amount_{transaction_type}_{transaction_id}"
                )
            )
        )


back_to_edit_amount = approve_transaction


async def get_new_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.effective_chat.type == Chat.PRIVATE
        and update.effective_user.id == Config.ADMIN_ID
    ):
        transaction_id = int(
            update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.split("_")[-1]
        )
        new_amount = float(update.message.text)
        with models.session_scope() as s:
            transaction = s.get(models.Transaction, transaction_id)
            transaction.amount = new_amount
            s.commit()
            await update.message.reply_to_message.delete()
            await update.message.reply_text(
                text="تم تعديل المبلغ بنجاح ✅",
            )
            await update.message.reply_text(
                text=str(transaction),
                reply_markup=InlineKeyboardMarkup(
                    [
                        build_process_deposit_options_keyboard(
                            transaction_id=transaction_id
                        ),
                        build_back_button(
                            data=f"back_to_handle_{transaction.type}_{transaction_id}"
                        ),
                    ]
                ),
            )


async def decline_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.effective_chat.type == Chat.PRIVATE
        and update.effective_user.id == Config.ADMIN_ID
    ):
        transaction_id = int(update.callback_query.data.split("_")[-1])
        transaction_type = update.callback_query.data.split("_")[-2]
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بسبب الرفض",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_row(
                build_back_button(
                    data=f"back_to_handle_{transaction_type}_{transaction_id}"
                )
            )
        )


async def get_decline_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.effective_chat.type == Chat.PRIVATE
        and update.effective_user.id == Config.ADMIN_ID
    ):
        transaction_id = int(
            update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.split("_")[-1]
        )
        reason = update.message.text
        with models.session_scope() as s:
            transaction = s.get(models.Transaction, transaction_id)
            transaction.status = "declined"
            transaction.decline_reason = reason
            s.commit()
            user = s.get(models.User, transaction.user_id)
            await TeleClientSingleton().send_message(
                entity=transaction.user_id,
                message=TEXTS[user.lang]["transaction_declined"].format(
                    TRANSACTION_TYPES[user.lang][transaction.type],
                    transaction.id,
                    reason,
                ),
                parse_mode="html",
            )
            await update.message.reply_to_message.edit_reply_markup(
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(
                        text="تم الرفض ❌",
                        callback_data="❌❌❌",
                    )
                )
            )
            await update.message.reply_text(
                text="تم الرفض ❌",
                reply_to_message_id=update.message.reply_to_message.id,
            )


async def back_to_handle_transaction(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if (
        update.effective_chat.type == Chat.PRIVATE
        and update.effective_user.id == Config.ADMIN_ID
    ):
        transaction_id = int(update.callback_query.data.split("_")[-1])
        transaction_type = update.callback_query.data.split("_")[-2]
        with models.session_scope() as s:
            transaction = s.get(models.Transaction, transaction_id)
            await update.callback_query.edit_message_text(
                text=str(transaction),
                reply_markup=InlineKeyboardMarkup(
                    build_process_transaction_keyboard(
                        transaction_type=transaction_type,
                        transaction_id=transaction_id,
                        lib="ptb",
                    )
                ),
            )


approve_transaction_handler = CallbackQueryHandler(
    approve_transaction,
    r"^approve_((deposit)|(withdraw))_",
)
confirm_approve_handler = CallbackQueryHandler(
    confirm_approve, r"^confirm_approve_deposit_"
)
get_proof_handler = MessageHandler(
    filters=filters.REPLY & filters.PHOTO & Proof(),
    callback=get_proof,
)
edit_amount_handler = CallbackQueryHandler(
    edit_amount,
    r"^edit_amount_((deposit)|(withdraw))",
)
get_new_amount_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & NewAmount(),
    callback=get_new_amount,
)
decline_transaction_handler = CallbackQueryHandler(
    decline_transaction,
    r"^decline_((deposit)|(withdraw))_",
)
get_decline_reason_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & DeclineReason(),
    callback=get_decline_reason,
)
back_to_handle_transaction_handler = CallbackQueryHandler(
    back_to_handle_transaction,
    r"^back_to_handle_((withdraw)|(deposit))",
)
back_to_edit_amount_handler = CallbackQueryHandler(
    back_to_edit_amount,
    r"^back_to_edit_amount",
)
