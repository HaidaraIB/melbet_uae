from telegram import Update
from telegram.ext.filters import UpdateFilter
import models


class NewAmount(UpdateFilter):
    def filter(self, update: Update):
        try:
            return update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.startswith("back_to_edit_amount_")
        except:
            return False


class Proof(UpdateFilter):
    def filter(self, update: Update):
        try:
            data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data
            return data.startswith("edit_amount_") or data.startswith(
                "back_to_handle_withdraw"
            )
        except:
            return False


class DeclineReason(UpdateFilter):
    def filter(self, update: Update):
        try:
            return update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.startswith("back_to_handle_")
        except:
            return False
