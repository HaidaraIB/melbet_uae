from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from TeleClientSingleton import TeleClientSingleton
import pandas as pd
from client.client_calls.constants import openai
from common.lang_dicts import *
from common.constants import TIMEZONE
from Config import Config
from datetime import datetime, timedelta
import io
import logging
import json
import models

log = logging.getLogger(__name__)


async def handle_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != Config.ACCOUNTS_GROUP_ID:
        return
    file = await update.message.document.get_file()

    # Download the file as bytes
    excel_data = io.BytesIO()
    await file.download_to_memory(out=excel_data)
    excel_data.seek(0)  # Reset pointer to start of file

    # Read Excel using pandas
    try:
        df = pd.read_excel(excel_data)

        # Convert to text (CSV or JSON)
        data_str = df.to_csv(index=False)

        # Send to OpenAI for analysis
        response = await openai.chat.completions.create(
            model=Config.GPT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful data analyst.",
                },
                {
                    "role": "user",
                    "content": (
                        f"Analyze this data:\n"
                        f"{data_str}\n"
                        "And respond ONLY with a JSON I can deal with\n"
                        "the JSON format I want:\n\n"
                        """
                        {
                            "metadata": {
                                "time_interval": {
                                    "start": "...",  // in ISO format
                                    "end": "..."     // in ISO format
                                },
                                "currency": "...",
                                "website_id": "...",
                                "campaign": "...",
                                "media_id": "...",
                                "affiliate_id": ..., // int
                                "new_players_only": ..., // bool
                                "non_depositing_players_only": ..., // bool
                                "generation_date": "..."  // in ISO format
                            },
                            "players": [
                                {
                                    "number": ..., // int
                                    "website_id": ..., // int
                                    "website": "...",
                                    "media_id": ..., // int
                                    "subid": ..., // int
                                    "click_id": ..., // int
                                    "player_id": ..., // int
                                    "registration_date": "...",  // in ISO format
                                    "country": "...", // either syr or uae
                                    "sum_of_all_deposits": ..., // int
                                    "total_bet_amount": ..., // int
                                    "bonus_amount": ..., // int
                                    "company_profit": ..., // int
                                    "rs": ..., // int
                                    "cpa": ..., // int
                                    "commission_amount": ..., // int
                                    "hold_time": ..., // int
                                    "blocked": ... // bool
                                }
                                ...
                            ],
                            "summary": {
                                "total_players": ..., // int
                                "total_deposits": ..., // int
                                "total_bets": ..., // int
                                "total_bonuses": ..., // int
                                "total_profit": ... // int
                            }
                        }
                        """
                    ),
                },
            ],
        )
        data = response.choices[0].message.content
        if "```json" in data:
            data = data.split("```json")[1].split("```")[0]
        parsed_data = json.loads(data)
        with models.session_scope() as s:
            for player in parsed_data["players"]:
                if isinstance(player["subid"], int) and isinstance(
                    player["player_id"], int
                ):
                    existing_account = (
                        s.query(models.PlayerAccount)
                        .filter_by(account_number=player["player_id"])
                        .first()
                    )
                    if not existing_account:
                        is_points = False
                        if player["subid"] < 0 and player["country"] == "uae":
                            is_points = True
                        player["subid"] = abs(player["subid"])
                        user = s.get(models.User, player["subid"])
                        if not user:
                            try:
                                u = await TeleClientSingleton().get_entity(
                                    entity=player["subid"]
                                )
                                user = models.User(
                                    user_id=player["subid"],
                                    username=u.username or "N/A",
                                    name=(u.first_name or "")
                                    + " "
                                    + (u.last_name or ""),
                                    lang=(
                                        models.Language.ARABIC
                                        if player["country"] == "syr"
                                        else models.Language.ENGLISH
                                    ),
                                    from_group_id=(
                                        Config.SYR_MONITOR_GROUP_ID
                                        if player["country"] == "syr"
                                        else Config.UAE_MONITOR_GROUP_ID
                                    ),
                                )
                            except KeyError:
                                continue
                            except ValueError:
                                user = models.User(
                                    user_id=player["subid"],
                                    username="N/A",
                                    name="N/A",
                                    lang=(
                                        models.Language.ARABIC
                                        if player["country"] == "syr"
                                        else models.Language.ENGLISH
                                    ),
                                    from_group_id=(
                                        Config.SYR_MONITOR_GROUP_ID
                                        if player["country"] == "syr"
                                        else Config.UAE_MONITOR_GROUP_ID
                                    ),
                                )
                            s.add(user)
                            s.commit()
                        user_accounts = (
                            s.query(models.PlayerAccount)
                            .filter_by(user_id=player["subid"])
                            .all()
                        )
                        if (
                            len(user_accounts) == 0
                            or len(user_accounts) == 1
                            and (
                                (
                                    not user_accounts[0].is_points
                                    and user_accounts[0].country == "syr"
                                    and is_points
                                )
                                or (
                                    user_accounts[0].is_points
                                    and player["country"] == "syr"
                                    and not is_points
                                )
                            )
                        ):
                            registration_date = datetime.fromisoformat(
                                player["registration_date"]
                            )
                            offer_start_date = datetime.fromisoformat(
                                player["registration_date"]
                            )
                            offer_expirity_date = (
                                datetime.fromisoformat(player["registration_date"])
                                + timedelta(days=10)
                            ).replace(tzinfo=TIMEZONE)
                            now = datetime.now(TIMEZONE)
                            s.add(
                                models.PlayerAccount(
                                    user_id=player["subid"],
                                    account_number=player["player_id"],
                                    country=player["country"],
                                    currency=(
                                        "syp"
                                        if (
                                            player["country"] == "syr" and not is_points
                                        )
                                        else "aed"
                                    ),
                                    is_points=is_points,
                                    registration_date=registration_date,
                                    offer_start_date=offer_start_date,
                                    offer_expiry_date=offer_expirity_date,
                                    offer_prize=(
                                        150000
                                        if (
                                            player["country"] == "syr" and not is_points
                                        )
                                        else 50
                                    ),
                                )
                            )
                            s.commit()
                            offer_text = "\n\n"
                            if offer_expirity_date > now:
                                if player["country"] == "syr":
                                    if user.lang == models.Language.ARABIC:
                                        offer_text += (
                                            "🎁 <b>عرض ترحيبي حصري للأعضاء الجدد في سوريا:</b>\n"
                                            "لديك 10 أيام من تاريخ تسجيلك لتحقيق الشروط التالية:\n\n"
                                            "1️⃣ قم بإجراء ٧ إيداعات في ٧ أيام مختلفة (خلال مدة ١٠ أيام فقط)\n"
                                            "2️⃣ يجب أن يكون مجموع كل الإيداعات معًا خلال هذه الفترة ٤٠٠ ألف ليرة سورية أو أكثر\n\n"
                                            "💸 عند تحقيق الشرطين، تحصل فورًا على ١٥٠ ألف ليرة سورية مال حقيقي تضاف إلى حسابك الأساسي مباشرة!\n\n"
                                            "⏳ ملاحظة: إذا لم تكمل الشروط خلال ١٠ أيام من التسجيل، ينتهي العرض تلقائيًا."
                                        )
                                    else:
                                        offer_text += (
                                            "🎁 <b>Exclusive Welcome Offer for New Members in Syria:</b>\n"
                                            "You have 10 days from your registration date to fulfill the following conditions:\n\n"
                                            "1️⃣ Make 7 deposits on 7 different days (within the 10-day period)\n"
                                            "2️⃣ The total amount of all deposits during this period must be 400,000 SYP or more\n\n"
                                            "💸 Once you complete both conditions, you will immediately receive 150,000 SYP in real cash credited directly to your main account!\n\n"
                                            "⏳ Note: If you do not complete the requirements within 10 days of registration, the offer will automatically expire."
                                        )
                                elif player["country"] == "uae":
                                    if not is_points:
                                        if user.lang == models.Language.ARABIC:
                                            offer_text += (
                                                "🎁 <b>عرض ترحيبي حصري للأعضاء الجدد:</b>\n"
                                                "لديك 10 أيام من تاريخ تسجيلك لتحقيق الشروط التالية:\n\n"
                                                "1️⃣ قم بإجراء ٧ إيداعات في ٧ أيام مختلفة (خلال مدة ١٠ أيام فقط)\n"
                                                "2️⃣ يجب أن يكون مجموع كل الإيداعات معًا خلال هذه الفترة ٢٠٠ درهم أو أكثر\n\n"
                                                "💸 عند تحقيق الشرطين، تحصل فورًا على ٥٠ درهم مال حقيقي تضاف إلى حسابك الأساسي مباشرة!\n\n"
                                                "⏳ ملاحظة: إذا لم تكمل الشروط خلال ١٠ أيام من التسجيل، ينتهي العرض تلقائيًا."
                                            )
                                        else:
                                            offer_text += (
                                                "🎁 <b>Exclusive Welcome Offer for New Members:</b>\n"
                                                "You have 10 days from your registration date to meet these requirements:\n\n"
                                                "1️⃣ Make 7 deposits on 7 different days (within a 10-day period)\n"
                                                "2️⃣ The total sum of all deposits during this period must be 200 AED or more\n\n"
                                                "💸 Once you complete both conditions, you will instantly receive 50 AED in real cash credited directly to your main account!\n\n"
                                                "⏳ Note: If you do not meet the requirements within 10 days of registration, the offer will automatically expire."
                                            )
                                    else:
                                        if user.lang == models.Language.ARABIC:
                                            offer_text += (
                                                "🎁 <b>عرض ترحيبي حصري للأعضاء الجدد:</b>\n"
                                                "لديك 10 أيام من تاريخ تسجيلك لتحقيق الشروط التالية:\n\n"
                                                "1️⃣ قم بإجراء ٧ إيداعات في ٧ أيام مختلفة (خلال مدة ١٠ أيام فقط)\n"
                                                "2️⃣ يجب أن يكون مجموع كل الإيداعات معًا خلال هذه الفترة ٢٠٠ نقطة أو أكثر\n\n"
                                                "💸 عند تحقيق الشرطين، تحصل فورًا على ٥٠ نقطة تضاف إلى حسابك الأساسي مباشرة!\n\n"
                                                "⏳ ملاحظة: إذا لم تكمل الشروط خلال ١٠ أيام من التسجيل، ينتهي العرض تلقائيًا."
                                            )
                                        else:
                                            offer_text += (
                                                "🎁 <b>Exclusive Welcome Offer for New Members:</b>\n"
                                                "You have 10 days from your registration date to fulfill the following conditions:\n\n"
                                                "1️⃣ Make 7 deposits on 7 different days (within the 10-day period)\n"
                                                "2️⃣ The total sum of all deposits during this period must be 200 points or more\n\n"
                                                "💸 Once you complete both conditions, you will immediately receive 50 points credited directly to your main account!\n\n"
                                                "⏳ Note: If you do not complete the requirements within 10 days of registration, the offer will automatically expire."
                                            )
                            try:
                                await TeleClientSingleton().send_message(
                                    entity=player["subid"],
                                    message=TEXTS[user.lang][
                                        "account_link_success"
                                    ].format(player["player_id"])
                                    + offer_text,
                                    parse_mode="html",
                                )
                            except ValueError:
                                await update.message.reply_text(
                                    text=f"خطأ في أرسال رسالة ربط الحساب {player['player_id']} إلى المستخدم <code>{player['subid']}</code>"
                                )
        await update.message.reply_text(text="تم ✅")
    except Exception as e:
        log.error(f"Error processing Excel: {e}")


handle_excel_handler = MessageHandler(
    filters=(
        filters.Document.FileExtension("xlsx")
        | filters.Document.FileExtension("xls")
        | filters.Document.FileExtension("xlsm")
    ),
    callback=handle_excel,
)
