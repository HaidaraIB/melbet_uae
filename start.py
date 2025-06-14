from telegram import Update, Chat, BotCommandScopeChat, Bot
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    Application,
    ConversationHandler,
)
import models
from custom_filters import Admin
from common.decorators import (
    check_if_user_banned_dec,
    add_new_user_dec,
    check_if_user_member_decorator,
)
from common.keyboards import build_user_keyboard, build_admin_keyboard
from common.common import check_hidden_keyboard, get_lang
from common.lang_dicts import TEXTS
from client.client_calls.common import resume_timers_on_startup
from client.client_calls.functions import load_session_data
from Config import Config


async def inits(app: Application):
    bot: Bot = app.bot
    tg_owner = await bot.get_chat(chat_id=Config.OWNER_ID)
    models.Plan.initialize()
    with models.session_scope() as s:
        owner = s.get(models.User, tg_owner.id)
        if not owner:
            s.add(
                models.User(
                    user_id=tg_owner.id,
                    username=tg_owner.username if tg_owner.username else "",
                    name=tg_owner.full_name,
                    is_admin=True,
                )
            )
        gpt_prompt = s.get(models.Setting, "gpt_prompt")
        if not gpt_prompt:
            default_prompt = (
                "Respond in English by default, but match the user's language (e.g., Arabic if the message is in Arabic). "
                "If analyzing a receipt, identify if it is a financial transaction and extract details like amount, transaction ID, payment method, and date if possible. "
                "If details are missing or the text contains unclear characters, inform the user that hiding required details or submitting unclear images may delay the deposit process. "
                "Request a clearer image or missing details if necessary. "
                "When requested, store the user's Player account number and verify it in future interactions. "
                "If the user provides a different account number, warn them that it does not match their default account and request confirmation to update it."
            )
            s.add(models.Setting(key="gpt_prompt", value=default_prompt))
    await resume_timers_on_startup()
    load_session_data()


async def set_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st_cmd = ("start", "start command")
    commands = [st_cmd]
    if Admin().filter(update):
        commands.append(("admin", "admin command"))
    await context.bot.set_my_commands(
        commands=commands, scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
    )


@add_new_user_dec
@check_if_user_banned_dec
@check_if_user_member_decorator
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await set_commands(update, context)
        lang = get_lang(update.effective_user.id)
        await update.message.reply_text(
            text=TEXTS[lang]["welcome_msg"],
            reply_markup=build_user_keyboard(lang),
        )
        return ConversationHandler.END


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await set_commands(update, context)
        await update.message.reply_text(
            text="أهلاً بك...",
            reply_markup=check_hidden_keyboard(context),
        )

        await update.message.reply_text(
            text="تعمل الآن كآدمن 🕹",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


start_command = CommandHandler(command="start", callback=start)
admin_command = CommandHandler(command="admin", callback=admin)
