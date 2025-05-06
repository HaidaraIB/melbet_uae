from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from common.keyboards import build_request_buttons
import os
import models
import uuid
from datetime import datetime


def check_hidden_keyboard(context: ContextTypes.DEFAULT_TYPE):
    if (
        not context.user_data.get("request_keyboard_hidden", None)
        or not context.user_data["request_keyboard_hidden"]
    ):
        context.user_data["request_keyboard_hidden"] = False
        request_buttons = build_request_buttons()
        reply_markup = ReplyKeyboardMarkup(request_buttons, resize_keyboard=True)
    else:
        reply_markup = ReplyKeyboardRemove()
    return reply_markup


def uuid_generator():
    return uuid.uuid4().hex


def create_folders():
    os.makedirs("data", exist_ok=True)


def get_lang(user_id: int):
    with models.session_scope() as s:
        return s.get(models.User, user_id).lang


def format_datetime(d: datetime):
    return d.strftime("%Y-%m-%d %H:%M:%S")
