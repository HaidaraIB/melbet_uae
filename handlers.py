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

from admin.admin_calls import *
from admin.admin_settings import *
from admin.broadcast import *
from admin.ban import *
from admin.prompt_settings import *

from client.client_calls import *

from models import init_db

from TeleClientSingleton import TeleClientSingleton

from MyApp import MyApp
from jobs import check_suspicious_users, send_periodic_messages

from datetime import time


def setup_and_run():
    create_folders()
    init_db()

    app = MyApp.build_app()

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
    )

    app.job_queue.run_repeating(
        callback=send_periodic_messages,
        interval=2 * 60 * 60,
        data="security_messages",
    )
    app.job_queue.run_repeating(
        callback=send_periodic_messages,
        interval=2 * 60 * 60,
        data="promotional",
    )
    app.job_queue.run_daily(
        callback=schedule_daily_fixtures,
        time=time(
            hour=0,
            minute=0,
            tzinfo=TIMEZONE,
        ),
    )

    tele_client = TeleClientSingleton()
    tele_client.add_event_handler(client_handler, events.NewMessage(incoming=True))
    tele_client.add_event_handler(
        end_session, events.NewMessage(outgoing=True, pattern="/end")
    )

    app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

    tele_client.disconnect()
