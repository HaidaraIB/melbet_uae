from telegram import (
    Update,
    Chat,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButtonRequestUsers,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from custom_filters import Admin
import models
from common.keyboards import (
    build_admin_keyboard,
    build_back_button,
    build_back_to_home_page_button,
)
from common.back_to_home_page import back_to_admin_home_page_handler
from start import admin_command

(
    USER_ID_TO_BAN_UNBAN,
    BAN_UNBAN_USER,
) = range(2)


async def ban_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.answer()
        await update.callback_query.delete_message()
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                "اختر حساب المستخدم الذي تريد حظره بالضغط على الزر أدناه\n\n"
                "يمكنك إرسال الid برسالة أيضاً\n\n"
                "أو إلغاء العملية بالضغط على /admin."
            ),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(
                            text="اختيار حساب مستخدم",
                            request_users=KeyboardButtonRequestUsers(
                                request_id=5, user_is_bot=False
                            ),
                        )
                    ]
                ],
                resize_keyboard=True,
            ),
        )
        return USER_ID_TO_BAN_UNBAN


async def user_id_to_ban_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if update.effective_message.users_shared:
            user_id = update.effective_message.users_shared.users[0].user_id
        else:
            user_id = int(update.effective_message.text)

        context.user_data["user_id_to_ban_unban"] = user_id
        with models.session_scope() as s:
            user = s.get(models.User, user_id)
            if not user:
                try:
                    user_chat = await context.bot.get_chat(chat_id=user_id)
                except:
                    await update.message.reply_text(
                        text=(
                            "لم يتم العثور على المستخدم ❌\n"
                            "تأكد من الآيدي أو من أن المستخدم قد بدأ محادثة مع البوت من قبل"
                        ),
                    )
                    return
                user = models.User(
                    user_id=user_chat.id,
                    username=user_chat.username if user_chat.username else "",
                    name=user_chat.full_name,
                )
                s.add(user)

            if user.is_banned:
                ban_button = [
                    InlineKeyboardButton(
                        text="فك الحظر 🔓",
                        callback_data=f"unban",
                    )
                ]
            else:
                ban_button = [
                    InlineKeyboardButton(
                        text="حظر 🔒",
                        callback_data=f"ban",
                    )
                ]
        keyboard = [
            ban_button,
            build_back_button("back_to_user_id_to_ban_unban"),
            build_back_to_home_page_button()[0],
        ]
        await update.message.reply_text(
            text="تم العثور على المستخدم ✅",
            reply_markup=ReplyKeyboardRemove(),
        )
        await update.message.reply_text(
            text="هل تريد",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return BAN_UNBAN_USER


back_to_user_id_to_ban_unban = ban_unban


async def ban_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        with models.session_scope() as s:
            s.query(models.User).filter(
                models.User.user_id == context.user_data["user_id_to_ban_unban"]
            ).update(
                {models.User.is_banned: update.callback_query.data.startswith("ban")}
            )

        await update.callback_query.edit_message_text(
            text="تمت العملية بنجاح ✅",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


ban_unban_user_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            ban_unban,
            "^ban_unban$",
        ),
    ],
    states={
        USER_ID_TO_BAN_UNBAN: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=user_id_to_ban_unban,
            ),
            MessageHandler(
                filters=filters.StatusUpdate.USERS_SHARED,
                callback=user_id_to_ban_unban,
            ),
        ],
        BAN_UNBAN_USER: [
            CallbackQueryHandler(
                ban_unban_user,
                "^((ban)|(unban))$",
            ),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_user_id_to_ban_unban,
            "^back_to_user_id_to_ban_unban$",
        ),
        admin_command,
        back_to_admin_home_page_handler,
    ],
)
