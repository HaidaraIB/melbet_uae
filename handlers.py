from telegram import Update
from telethon import events
from start import start_command, admin_command
from common.common import create_folders
from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_user_home_page_handler,
)
from common.error_handler import error_handler
from common.force_join import check_joined_handler
from common.constants import TIMEZONE

from utils.api_calls import schedule_daily_fixtures

from user.user_calls import *
from user.user_settings import *
from user.analyze_game import *
from user.buy_voucher import *
from user.our_plans import *
from user.account_settings import *

from admin.admin_calls import *
from admin.admin_settings import *
from admin.broadcast import *
from admin.ban import *
from admin.prompt_settings import *
from admin.test_settings import *
from admin.plans_settings import *

from groups.group_preferences import *
from groups.groups_subs import *

from client.client_calls import *

from models import init_db

from TeleClientSingleton import TeleClientSingleton
from Config import Config

from MyApp import MyApp
from jobs import check_suspicious_users, send_periodic_messages

from datetime import time


def setup_and_run():
    create_folders()
    init_db()

    app = MyApp.build_app()

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

    app.add_handler(broadcast_message_handler)

    app.add_handler(check_joined_handler)

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

    app.add_error_handler(error_handler)

    app.job_queue.run_repeating(
        callback=check_suspicious_users,
        interval=2 * 60 * 60,
        job_kwargs={
            "id": "check_suspicious_users",
            "replace_existing": True,
        },
    )

    app.job_queue.run_repeating(
        callback=send_periodic_messages,
        interval=2 * 60 * 60,
        data="security_messages",
        job_kwargs={
            "id": "send_periodic_security_messages",
            "replace_existing": True,
        },
    )
    app.job_queue.run_repeating(
        callback=send_periodic_messages,
        interval=2 * 60 * 60,
        data="promotional",
        job_kwargs={
            "id": "send_periodic_promotional_messages",
            "replace_existing": True,
        },
    )
    app.job_queue.run_daily(
        callback=schedule_daily_fixtures,
        time=time(
            hour=0,
            minute=0,
            tzinfo=TIMEZONE,
        ),
        job_kwargs={
            "id": "schedule_daily_fixtures",
            "replace_existing": True,
        },
    )

    # app.job_queue.run_daily(
    #     callback=update_team_results,
    #     time=time(
    #         hour=3,
    #         minute=0,
    #         tzinfo=TIMEZONE,
    #     ),
    #     job_kwargs={
    #         "id": "daily_team_results_update",
    #         "replace_existing": True,
    #     },
    # )
    # app.job_queue.run_daily(
    #     callback=cache_monthly_fixtures,
    #     time=time(
    #         hour=1,
    #         minute=0,
    #         tzinfo=TIMEZONE,
    #     ),
    #     job_kwargs={
    #         "id": "cache_monthly_fixtures",
    #         "replace_existing": True,
    #     },
    # )

    # app.job_queue.run_once(
    #     callback=cache_monthly_fixtures,
    #     when=20,
    # )
    # app.job_queue.run_once(
    #     callback=schedule_daily_fixtures,
    #     when=20,
    # )

    tele_client = TeleClientSingleton()
    tele_client.add_event_handler(
        create_account,
        events.NewMessage(
            chats=Config.MONITOR_GROUP_ID,
            pattern=f".*((انشاء حساب)|(إنشاء حساب)|(حساب)|(account)|(Account)|(create account)|(Create account)|(create Account)|(Create Account)).*",
        ),
    )
    tele_client.add_event_handler(client_handler, events.NewMessage(incoming=True))
    tele_client.add_event_handler(
        end_session, events.NewMessage(outgoing=True, pattern="/end")
    )

    app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

    tele_client.disconnect()
