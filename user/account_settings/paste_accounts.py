from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from TeleClientSingleton import TeleClientSingleton
import pandas as pd
from client.client_calls.common import openai
from common.lang_dicts import *
from Config import Config
from datetime import datetime
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
                                "country": "...",
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
                        if (
                            player["subid"] < 0
                            and player["country"] == "United Arab Emirates"
                        ):
                            is_points = True
                        player["subid"] = abs(player["subid"])
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
                                    and user_accounts[0].country == "Syria"
                                    and is_points
                                )
                                or (
                                    user_accounts[0].is_points
                                    and player["country"] == "Syria"
                                    and not is_points
                                )
                            )
                        ):
                            user = s.get(models.User, player["subid"])
                            if not user:
                                u = await TeleClientSingleton().get_entity(
                                    entity=player["subid"]
                                )
                                user = models.User(
                                    user_id=player["subid"],
                                    username=u.username or "N/A",
                                    name=(u.first_name or "")
                                    + " "
                                    + (u.last_name or ""),
                                )
                                s.add(user)
                                s.commit()
                            s.add(
                                models.PlayerAccount(
                                    user_id=player["subid"],
                                    account_number=player["player_id"],
                                    country=player["country"],
                                    currency=(
                                        "syp" if player["country"] == "Syria" else "aed"
                                    ),
                                    registration_date=datetime.fromisoformat(
                                        player["registration_date"]
                                    ),
                                    is_points=is_points,
                                )
                            )
                            s.commit()
                            await TeleClientSingleton().send_message(
                                entity=player["subid"],
                                message=TEXTS[user.lang]["account_link_success"].format(
                                    player["player_id"]
                                ),
                            )
        await update.message.reply_text(text="تم ✅")
    except Exception as e:
        log.error(f"Error processing Excel: {e}")


handle_excel_handler = MessageHandler(
    filters=(
        filters.Document.FileExtension("xlsx")
        | filters.Document.FileExtension("xls ")
        | filters.Document.FileExtension("xlsm ")
    ),
    callback=handle_excel,
)
