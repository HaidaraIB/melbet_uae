from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from common.keyboards import build_back_button, build_back_to_home_page_button
from common.common import get_lang
from common.lang_dicts import *

AMOUNT, DURATION_TYPE, DURATION_VALUE, ODDS = range(4)

TOKEN = "YOUR_TOKEN_HERE"


# Step 1: Buy voucher button
async def buy_voucher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["send_voucher_odd_number"],
            reply_markup=InlineKeyboardMarkup(
                build_back_to_home_page_button(lang=lang, is_admin=False)
            ),
        )
        return AMOUNT


# Step 2: Enter amount
async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        keyboard = [
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["duration_days"], callback_data="duration_days"
                ),
                InlineKeyboardButton(
                    text=BUTTONS[lang]["duration_hours"], callback_data="duration_hours"
                ),
            ],
            build_back_button(data="back_to_get_amount", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False),
        ]
        if update.message:
            context.user_data["amount"] = update.message.text.strip()
            await update.message.reply_text(
                text=TEXTS[lang]["choose_duration_type"],
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["choose_duration_type"],
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return DURATION_TYPE


# Step 3: Choose duration type
async def get_duration_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button(data="back_to_get_duration_type", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False),
        ]
        if not update.callback_query.data.startswith("back"):
            duration_type = update.callback_query.data.replace("duration_", "")
            context.user_data["duration_type"] = duration_type
            if duration_type == "hours":
                msg = TEXTS[lang]["send_duration_hours"]
            else:
                msg = TEXTS[lang]["send_durstion_days"]

            await update.callback_query.edit_message_text(
                text=msg,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
    return DURATION_VALUE


# Step 4: Enter duration value
async def get_duration_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        lang = get_lang(update.effective_user.id)
        try:
            value = int(update.message.text.strip())
            if context.user_data["duration_type"] == "hours" and not (1 <= value <= 72):
                await update.message.reply_text(
                    "Please enter a number between 1 and 72."
                )
                return DURATION_VALUE

            context.user_data["duration_value"] = value
            await update.message.reply_text("Enter the odds you want (e.g. 2.5):")
            return ODDS
        except ValueError:
            await update.message.reply_text("Please enter a valid number.")
            return DURATION_VALUE


# Step 5: Enter odds and calculate price
async def get_odds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        odds = float(update.message.text.strip())
        context.user_data["odds"] = odds

        amount = context.user_data["amount"]
        duration = f"{context.user_data['duration_value']} {context.user_data['duration_type']}"
        price = round(odds * 5, 2)

        summary = (
            f"Voucher Summary\n"
            f"- Amount: {amount} AED\n"
            f"- Duration: {duration}\n"
            f"- Odds: {odds}\n"
            f"- Price: {price} AED\n\n"
            f"Do you want to continue to payment?"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Continue to Payment", callback_data="confirm_payment"
                ),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_voucher"),
            ]
        ]

        await update.message.reply_text(
            summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Please enter a valid number for odds.")
        return ODDS


# Step 6: Handle confirm/cancel
async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "confirm_payment":
        await query.message.edit_text("✅ Payment processing... (This is a mock step)")
    else:
        await query.message.edit_text("❌ Voucher cancelled.")
    return ConversationHandler.END


# Cancel fallback
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


# Main entry point
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(buy_voucher, pattern="^buy_voucher$")],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            DURATION_TYPE: [
                CallbackQueryHandler(get_duration_type, pattern="^duration_")
            ],
            DURATION_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_duration_value)
            ],
            ODDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_odds)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(
        CallbackQueryHandler(
            handle_payment, pattern="^(confirm_payment|cancel_voucher)$"
        )
    )

    print("Bot is running...")
    app.run_polling()


if name == "main":
    main()
