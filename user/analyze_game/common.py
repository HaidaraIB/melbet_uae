from Config import Config
from client.client_calls.constants import openai
from common.lang_dicts import *
import stripe
import aiohttp
import json
import models


async def generate_gpt_analysis(match_info: dict):
    prompt = (
        "You are a professional football analyst.\n\n"
        "Based on the match data and ALL available betting markets provided below, generate exactly 3 smart betting suggestions, each from a DIFFERENT market type (for example: 1X2, Asian Handicap, Total Goals, Cards, Corners, Goal Method, Player to Score, etc. — only from the markets present in the data).\n\n"
        "You MUST use a different market for each suggestion. Do NOT repeat any market type in your main picks. Select from the actual markets and odds provided below.\n\n"
        "Each suggestion must include:\n"
        "- Title (e.g., PSG to Win, Over 3.5 Cards, Lautaro Martinez to Score)\n"
        "- Market Type (exactly as it appears in the data)\n"
        "- Risk Level (Low, Medium, High)\n"
        "- Estimated Probability (in %)\n"
        "- Actual Market Odds (from bookmakers)\n"
        "- Value assessment: compare your probability with implied odds, and mark as ✅ (Value), ⚠️ (Fair), or ❌ (No value)\n"
        "- Reason (max 3 lines, based strictly on provided stats and match data)\n\n"
        "Then provide the following additional sections:\n"
        "4. Optional Combo Bet (if at least 2 suggestions logically align). Show combined odds and reasoning.\n"
        "5. One 'Avoid this Bet' suggestion (pick the riskiest or least valuable bet from available markets).\n"
        "6. Value Indicator for each bet: ✅ (Value), ⚠️ (Fair), ❌ (No value)\n"
        "7. Recap Summary Table for this match:\n"
        "   - Best Value Bet\n"
        "   - Safest Bet\n"
        "   - Highest Payout Potential\n\n"
        "STRICT INSTRUCTIONS:\n"
        "- Use ONLY the markets and odds provided below, do NOT invent or generalize.\n"
        "- Each main suggestion must use a different market type (e.g., not three 'Goals Over/Under' bets).\n"
        "- Reasons must cite specific stats, form, or odds from the data provided.\n"
        "- Do NOT use combo bets in the 3 main suggestions.\n"
        "- Format using Telegram Markdown (bullets, bold, icons, etc.).\n\n"
        "Match Summary:\n"
        f"- Teams: {match_info['teams']}\n"
        f"- Date: {match_info['date']}\n"
        f"- League: {match_info['league']}\n"
        f"- Venue: {match_info['venue']}\n\n"
        f"Bookmaker Odds:\n{match_info['odds']}\n\n"
        f"Last 5 Head-to-Head Matches:\n{match_info['h2h']}\n\n"
        f"Last 5 Matches:\n"
        f"{match_info['home_name']}:\n{match_info['home_last']}\n"
        f"{match_info['away_name']}:\n{match_info['away_last']}\n\n"
        f"Standings:\n"
        f"{match_info['home_name']}: {match_info['home_rank']}\n"
        f"{match_info['away_name']}: {match_info['away_rank']}\n\n"
        f"Injuries:\n"
        f"{match_info['home_name']}:\n{match_info['home_inj']}\n"
        f"{match_info['away_name']}:\n{match_info['away_inj']}\n\n"
        "Output Format:\n"
        "- Use English and Telegram Markdown formatting\n"
        "- Use 🔹 / 🔸 / 🔺 icons for Low / Medium / High risk\n"
        "- Bold the suggestion titles\n"
        "- Use bullet points for: Market, Probability, Odds, Value, Reason\n"
    )
    response = await openai.chat.completions.create(
        model=Config.GPT_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
    # response = await openai.responses.create(
    #     model="o3-pro",
    #     input=[
    #         {
    #             "role": "user",
    #             "content": prompt,
    #         }
    #     ],
    #     temperature=0.7,
    # )
    # return response.output_text


async def ask_gpt_about_match(teams: str, sport: str):
    prompt = f"In {sport} extract clearly from {teams} the two team names in lower case English letters. the priority is for the most famous teams. Return as JSON with: team1, team2 "
    response = await openai.chat.completions.create(
        model=Config.GPT_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )
    return response.choices[0].message.content.replace("json", "").replace("```", "")


def generate_stripe_payment_link(
    uid: int, match_id: int, amount: int = 1000, currency: str = "aed"
):
    price = stripe.Price.create(
        currency=currency,
        unit_amount=amount,
        product_data={
            "name": f"Match Analysis #{match_id}",
        },
    )

    payment_link = stripe.PaymentLink.create(
        line_items=[
            {
                "price": price.id,
                "quantity": 1,
            }
        ],
        payment_intent_data={
            "metadata": {
                "telegram_id": str(uid),
                "match_id": str(match_id),
            }
        },
        after_completion={
            "type": "redirect",
            "redirect": {"url": "https://t.me/TipsterHubBot"},
        },
    )

    return {
        "url": payment_link.url,
        "id": payment_link.id,
    }


async def check_stripe_payment_webhook(
    uid: int, match_id: int, price: float = 10, currency: str = "aed"
):
    url = f"https://webhook.site/token/{Config.WEBHOOK_TOKEN}/requests"
    headers = {
        "Api-Key": Config.WEBHOOK_API_KEY,
    }
    params = {"sorting": "newest"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    for req in data["data"]:
                        try:
                            if not req["user_agent"].lower().startswith("stripe"):
                                continue
                            body = json.loads(req.get("content", ""))
                            meta = body["data"]["object"]["metadata"]
                            if (
                                meta.get("telegram_id") == str(uid)
                                and meta.get("match_id") == str(match_id)
                                and body["type"] == "payment_intent.succeeded"
                                and int(body["data"]["object"]["amount"])
                                == int(price * 100)
                                and body["data"]["object"]["currency"].lower()
                                == currency.lower()
                            ):
                                with models.session_scope() as s:
                                    transaction = (
                                        s.query(models.Transaction)
                                        .filter_by(
                                            receipt_id=body["data"]["object"]["id"]
                                        )
                                        .first()
                                    )
                                    if not transaction:
                                        s.add(
                                            models.Transaction(
                                                receipt_id=body["data"]["object"]["id"],
                                                user_id=uid,
                                                type="analyze_game",
                                                amount=float(
                                                    data["data"]["object"]["amount"]
                                                    / 100
                                                ),
                                                currency=currency,
                                                status="approved",
                                            )
                                        )
                                        s.commit()
                                stripe.PaymentLink.modify(
                                    id=body["data"]["object"]["id"], active=False
                                )
                                return body
                        except Exception as e:
                            continue
        return False

    except Exception as e:
        return False


# 3. دالة بدء تحليل المباراة بعد التحقق من الدفع
async def start_match_analysis_if_paid(uid: int, match_id: int):
    payment_data = await check_stripe_payment_webhook(uid, match_id)
    if payment_data:
        # من هنا تبدأ عملية تحليل المباراة وربطها بالمستخدم
        # يمكنك إضافة كودك هنا لإرسال النتائج أو حفظها في قاعدة البيانات
        print(f"تم الدفع بنجاح للمستخدم {uid} للمباراة {match_id}. ابدأ التحليل!")
        # ...
        return True
    return False
