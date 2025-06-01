from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus
from groups.constants import *
from groups.lang_dicts import *


async def check_admin(
    context: ContextTypes.DEFAULT_TYPE,
    group_id: int,
    user_id: int,
    lang: Language,
):
    member = await context.bot.get_chat_member(group_id, user_id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await context.bot.send_message(
            chat_id=group_id,
            text=TEXTS[lang]["admin_only"],
        )
        return False
    return True


def construct_prefs_summary(prefs: dict, lang: Language):
    l = prefs["language"]
    d = prefs["dialect"]
    if lang == Language.ARABIC:
        text = (
            f"إعدادات الغروب:\n"
            f"- اللغة: {LANGUAGES.get(l, l)}\n"
            f"- اللهجة: {DIALECTS[l].get(d, d)}\n"
            f"- الرياضات والدوريات:\n"
        )
        for sport, leagues in prefs["sports"].items():
            text += f"  • {SPORTS[sport][lang]}: "
            league_names = [
                league["name"]
                for league in LEAGUES[sport].values()
                if league["id"] in leagues
            ]
            text += ", ".join(league_names) or "كل الدوريات"
            text += "\n"
        text += "\n احفظ هذه التفضيلات؟ ✅"
    elif lang == Language.ENGLISH:
        text = (
            f"Group Settings:\n"
            f"- Language: {LANGUAGES.get(l, l)}\n"
            f"- Dialect: {DIALECTS[l].get(d, d)}\n"
            f"- Sports and leagues:\n"
        )
        for sport, leagues in prefs["sports"].items():
            text += f"  • {SPORTS[sport][lang]}: "
            league_names = [
                league["name"]
                for league in LEAGUES[sport].values()
                if league["id"] in leagues
            ]
            text += ", ".join(league_names) or "All leagues"
            text += "\n"
        text += "\n Save these preferences? ✅"

    return text
