from telegram import Update, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
from custom_filters import Admin

from utils.api_calls import (
    _send_pre_match_lineup,
    _send_post_match_stats,
    _extract_fixture_data,
)
from utils.helpers import HEADERS, BASE_URL
from common.keyboards import build_back_to_home_page_button
import logging
import aiohttp

log = logging.getLogger(__name__)


def build_test_settings_keyboard():
    return [
        [
            InlineKeyboardButton(
                text="التشكيلة 👥",
                callback_data="test_match_lineup",
            ),
            InlineKeyboardButton(
                text="الإحصائيات 📊",
                callback_data="test_match_stats",
            ),
        ]
    ]


async def test_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = build_test_settings_keyboard()
        keyboard.append(build_back_to_home_page_button()[0])
        await update.callback_query.edit_message_text(
            text="اختر أحد الخيارات التالية",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def test_match_lineup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{BASE_URL}/fixtures",
                    params={"id": 1208814},
                    headers=HEADERS,
                ) as response:
                    data = await response.json()
            fixture = data["response"]
            if fixture:
                fixtrue_data = _extract_fixture_data(fixture=fixture[0])
                await _send_pre_match_lineup(match=fixtrue_data, context=context)
            await update.callback_query.answer(
                text="تمت العملية بنجاح ✅",
                show_alert=True,
            )
        except Exception as e:
            log.error(f"Error testing match lineup: {e}")
            await update.callback_query.answer(
                text="خطأ ❗️",
                show_alert=True,
            )


async def test_match_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        try:
            await _send_post_match_stats(context=context, fixture_id=1208814)
            await update.callback_query.answer(
                text="تمت العملية بنجاح ✅",
                show_alert=True,
            )
        except Exception as e:
            log.error(f"Error testing match lineup: {e}")
            await update.callback_query.answer(
                text="خطأ ❗️",
                show_alert=True,
            )


test_settings_handler = CallbackQueryHandler(test_settings, "^test_settings$")

test_match_lineup_handler = CallbackQueryHandler(
    test_match_lineup, "^test_match_lineup$"
)
test_match_stats_handler = CallbackQueryHandler(test_match_stats, "^test_match_stats$")
