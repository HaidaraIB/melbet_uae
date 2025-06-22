from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telethon import events
from start import start_command, admin_command
from common.common import create_folders
from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_user_home_page_handler,
)
from common.error_handler import error_handler
from common.constants import TIMEZONE

from utils.api_calls import schedule_daily_fixtures
from utils.cache import cache_monthly_fixtures

from user.user_calls import *
from user.user_settings import *
from user.analyze_game import *
from user.buy_voucher import *
from user.our_plans import *
from user.account_settings import *
from user.my_transactions import *

from admin.admin_calls import *
from admin.admin_settings import *
from admin.broadcast import *
from admin.ban import *
from admin.prompt_settings import *
from admin.test_settings import *
from admin.plans_settings import *
from admin.payment_methods import *

from groups.group_preferences import *
from groups.groups_subs import *

from client.client_calls import *

from models import init_db

from TeleBotSingleton import TeleBotSingleton
from TeleClientSingleton import TeleClientSingleton
from Config import Config

from MyApp import MyApp
from jobs import (
    check_suspicious_users,
    send_periodic_messages,
    match_recipts_with_transaction,
)

from datetime import time
import re


def setup_and_run():
    create_folders()
    init_db()

    app = MyApp.build_app()

    app.add_handler(my_transactions_handler)

    app.add_handler(handle_excel_handler)

    app.add_handler(group_settings_handler)

    app.add_handler(our_plans_handler)

    app.add_handler(buy_voucher_handler)

    app.add_handler(analyze_game_handler)

    app.add_handler(plans_settings_handler)

    app.add_handler(test_match_stats_handler)
    app.add_handler(test_match_lineup_handler)
    app.add_handler(test_settings_handler)

    app.add_handler(user_settings_handler)
    app.add_handler(change_lang_handler)

    app.add_handler(prompt_settings_handler)

    # ADMIN SETTINGS
    app.add_handler(show_admins_handler)
    app.add_handler(add_admin_handler)
    app.add_handler(remove_admin_handler)
    app.add_handler(admin_settings_handler)

    app.add_handler(add_payment_method_handler)
    app.add_handler(payment_method_settings_handler)
    app.add_handler(show_payment_methods_handler)
    app.add_handler(update_payment_method_handler)

    app.add_handler(approve_transaction_handler)
    app.add_handler(get_proof_handler)
    app.add_handler(edit_amount_handler)
    app.add_handler(get_new_amount_handler)
    app.add_handler(decline_transaction_handler)
    app.add_handler(get_decline_reason_handler)
    app.add_handler(back_to_edit_amount_handler)
    app.add_handler(back_to_handle_transaction_handler)

    app.add_handler(broadcast_message_handler)

    app.add_handler(ban_unban_user_handler)

    app.add_handler(groups_settings_handler)
    app.add_handler(show_group_details_handler)
    app.add_handler(confirm_group_payment_handler)
    app.add_handler(renew_group_sub_handler)
    app.add_handler(activate_sub_handler)
    app.add_handler(deactivate_sub_handler)
    app.add_handler(activate_group_handler)

    app.add_handler(admin_command)
    app.add_handler(start_command)
    app.add_handler(find_id_handler)
    app.add_handler(hide_ids_keyboard_handler)
    app.add_handler(back_to_user_home_page_handler)
    app.add_handler(back_to_admin_home_page_handler)

    app.add_handler(
        MessageHandler(
            filters=filters.StatusUpdate.NEW_CHAT_MEMBERS,
            callback=handle_new_user,
        )
    )

    app.add_error_handler(error_handler)

    app.job_queue.run_repeating(
        callback=match_recipts_with_transaction,
        interval=600,
        job_kwargs={
            "id": "match_recipts_with_transaction",
            "replace_existing": True,
        },
    )

    app.job_queue.run_repeating(
        callback=check_suspicious_users,
        interval=2 * 60 * 60,
        data={
            "chat_id": Config.UAE_MONITOR_GROUP_ID,
        },
        job_kwargs={
            "id": "check_suspicious_users_uae",
            "replace_existing": True,
        },
    )
    app.job_queue.run_repeating(
        callback=check_suspicious_users,
        interval=2 * 60 * 60,
        data={
            "chat_id": Config.SYR_MONITOR_GROUP_ID,
        },
        job_kwargs={
            "id": "check_suspicious_users_syr",
            "replace_existing": True,
        },
    )

    app.job_queue.run_repeating(
        callback=send_periodic_messages,
        interval=3 * 60 * 60,
        data={
            "topic": "security_messages",
        },
        job_kwargs={
            "id": "send_periodic_security_messages",
            "replace_existing": True,
        },
    )
    app.job_queue.run_repeating(
        callback=send_periodic_messages,
        interval=3 * 60 * 60,
        data={
            "topic": "promotional",
        },
        job_kwargs={
            "id": "send_periodic_promotional",
            "replace_existing": True,
        },
    )
    app.job_queue.run_repeating(
        callback=send_periodic_messages,
        interval=3 * 60 * 60,
        data={
            "topic": "dp_wd_instructions",
        },
        job_kwargs={
            "id": "send_periodic_dp_wd_instructions",
            "replace_existing": True,
        },
    )

    app.job_queue.run_daily(
        callback=schedule_daily_fixtures,
        time=time(hour=0, minute=0, tzinfo=TIMEZONE),
        job_kwargs={
            "id": "schedule_daily_fixtures",
            "replace_existing": True,
        },
    )

    app.job_queue.run_daily(
        callback=cache_monthly_fixtures,
        time=time(hour=1, minute=0, tzinfo=TIMEZONE),
        job_kwargs={
            "id": "cache_monthly_fixtures",
            "replace_existing": True,
        },
    )

    tele_client = TeleClientSingleton()
    # monitor
    tele_client.add_event_handler(
        create_account,
        events.NewMessage(
            chats=[Config.UAE_MONITOR_GROUP_ID, Config.SYR_MONITOR_GROUP_ID],
            pattern=r".*?([اإ]نشاء\s+حساب|حساب|[aA]ccount|[cC]reate\s+[aA]ccount|[Pp]oints?|نقاط)",
            incoming=True,
        ),
    )
    tele_client.add_event_handler(
        listen_to_dp_and_wd_requests,
        events.NewMessage(
            chats=[Config.UAE_MONITOR_GROUP_ID, Config.SYR_MONITOR_GROUP_ID],
            incoming=True,
        ),
    )
    # private
    tele_client.add_event_handler(
        respond_in_private,
        events.NewMessage(incoming=True),
    )
    tele_client.add_event_handler(
        end_session,
        events.NewMessage(pattern="/end", outgoing=True),
    )
    tele_client.add_event_handler(
        get_receipt,
        events.NewMessage(incoming=True),
    )
    tele_client.add_event_handler(
        get_missing,
        events.NewMessage(incoming=True),
    )

    tele_bot = TeleBotSingleton()
    tele_bot.add_event_handler(
        send_transaction_to_proccess,
        events.CallbackQuery(pattern=r"^send_transaction_to_proccess$"),
    )
    tele_bot.add_event_handler(
        paste_receipte,
        events.NewMessage(chats=Config.RECEIPTS_GROUP_ID, incoming=True),
    )
    tele_bot.add_event_handler(
        choose_payment_method,
        events.CallbackQuery(
            pattern=r"^((deposit)|(withdraw))_session_payment_method_"
        ),
    )
    tele_bot.add_event_handler(
        choose_account_number,
        events.CallbackQuery(
            pattern=r"^((deposit)|(withdraw))_session_player_account_"
        ),
    )
    tele_bot.add_event_handler(
        check_payment,
        events.CallbackQuery(pattern=r"^payment_done$"),
    )

    app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

    tele_client.disconnect()
    tele_bot.disconnect()


async def handle_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in [
        Config.UAE_MONITOR_GROUP_ID,
        Config.SYR_MONITOR_GROUP_ID,
    ]:
        return

    with models.session_scope() as s:
        for user in update.message.new_chat_members:
            existing_user = (
                s.query(models.User).filter(models.User.user_id == user.id).first()
            )
            if not existing_user:
                new_user = models.User(
                    user_id=user.id,
                    username=user.username,
                    name=user.full_name,
                    lang=(
                        models.Language.ARABIC
                        if update.effective_chat.id == Config.SYR_MONITOR_GROUP_ID
                        else models.Language.ENGLISH
                    ),
                    from_group_id=update.effective_chat.id,
                )
                s.add(new_user)
                s.commit()
