from TeleClientSingleton import TeleClientSingleton
from Config import Config
from common.constants import TIMEZONE
from client.client_calls.constants import openai
from client.client_calls.lang_dicts import TEXTS
from utils.api_calls_by_sport import get_fixtures_by_sport
import utils.api_calls as api_calls
from utils.functions import (
    format_basketball_stats,
    format_american_football_stats,
    format_hockey_stats,
    format_football_stats,
    format_last_matches,
    structure_team_standing,
    summarize_odds,
    filter_fixtures,
)
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import models
import stripe
import aiohttp
import random
import logging

log = logging.getLogger(__name__)


async def summarize_fixtures_with_odds_stats(fixtures: list) -> str:
    summary = ""
    for fix in fixtures:
        fix_summary = ""
        fixture_id = fix["fixture_id"]
        home_name = fix["home_name"]
        home_id = fix["home_id"]
        away_name = fix["away_name"]
        away_id = fix["away_id"]
        league_id = fix["league_id"]
        league_name = fix["league_name"]
        date = fix["date"][:16].replace("T", " ")
        season = fix["season"]
        fix_summary += f"\n=== Home Team: {home_name} vs Away Team: {away_name} | {league_name} | {date} ===\n"

        # STANDINGS
        with models.session_scope() as session:
            home_stand_obj = (
                session.query(models.CachedStandings)
                .filter_by(
                    team_id=home_id,
                    league_id=league_id,
                    season=season,
                    sport=fix["sport"],
                )
                .first()
            )
            home_stand = structure_team_standing(
                data=home_stand_obj.data if home_stand_obj else None, sport=fix["sport"]
            )
            away_stand_obj = (
                session.query(models.CachedStandings)
                .filter_by(
                    team_id=away_id,
                    league_id=league_id,
                    season=season,
                    sport=fix["sport"],
                )
                .first()
            )
            away_stand = structure_team_standing(
                data=away_stand_obj.data if away_stand_obj else None, sport=fix["sport"]
            )

        if home_stand and away_stand:
            fix_summary += "Standings:\n"
            fix_summary += f"- {home_name}: Rank {home_stand['rank']} | {home_stand['points']} pts\n"
            fix_summary += f"- {away_name}: Rank {away_stand['rank']} | {away_stand['points']} pts\n"
        else:
            fix_summary += "Standings: Not available\n"

        # ODDS
        with models.session_scope() as session:
            odds_obj = (
                session.query(models.CachedOdds)
                .filter_by(fixture_id=fixture_id, sport=fix["sport"])
                .first()
            )
            odds = odds_obj.data if odds_obj else None
        fix_summary += summarize_odds(odds) if odds else "- Odds not available\n"

        # TEAMS STATS
        with models.session_scope() as session:
            home_stats_obj = (
                session.query(models.CachedTeamStats)
                .filter_by(
                    team_id=home_id,
                    league_id=league_id,
                    season=season,
                    sport=fix["sport"],
                    game_id=fixture_id,
                )
                .first()
            )
            home_stats = home_stats_obj.data if home_stats_obj else None
            away_stats_obj = (
                session.query(models.CachedTeamStats)
                .filter_by(
                    team_id=away_id,
                    league_id=league_id,
                    season=season,
                    sport=fix["sport"],
                    game_id=fixture_id,
                )
                .first()
            )
            away_stats = away_stats_obj.data if away_stats_obj else None
        if home_stats or away_stats:
            if home_stats:
                fix_summary += f"\n{home_name} Statistics:\n"
                if fix["sport"] == "basketball":
                    home_formatted = format_basketball_stats(stats=home_stats)
                elif fix["sport"] == "football":
                    home_formatted = format_football_stats(stats=home_stats)
                elif fix["sport"] == "american-football":
                    home_formatted = format_american_football_stats(stats=home_stats)
                elif fix["sport"] == "hockey":
                    home_formatted = format_hockey_stats(stats=home_stats)

                fix_summary += (
                    f"- {home_name}: {home_formatted}\n"
                    if home_formatted
                    else f"- {home_name}: Stats unavailable\n"
                )
            if away_stats:
                fix_summary += f"\n{away_name} Statistics:\n"
                if fix["sport"] == "basketball":
                    away_formatted = format_basketball_stats(stats=away_stats)
                elif fix["sport"] == "football":
                    away_formatted = format_football_stats(stats=away_stats)
                elif fix["sport"] == "american-football":
                    away_formatted = format_american_football_stats(stats=away_stats)
                elif fix["sport"] == "hockey":
                    away_formatted = format_hockey_stats(stats=away_stats)

                fix_summary += (
                    f"- {away_name}: {away_formatted}\n"
                    if away_formatted
                    else f"- {away_name}: Stats unavailable\n"
                )
        else:
            fix_summary += "\nTeam Statistics: Not available\n"

        # FB FIXTURE STATS
        if fix["sport"] == "football":
            with models.session_scope() as session:
                fix_stats_obj = (
                    session.query(models.CachedFixtureStats)
                    .filter_by(fixture_id=fixture_id, sport=fix["sport"])
                    .first()
                )
                fix_stats = fix_stats_obj.data if fix_stats_obj else None
            if fix_stats:
                fix_summary += "\nMatch Stats:\n"
                for team_stats in fix_stats:
                    team_name = team_stats["team"]["name"]
                    stats_lines = [
                        f"  • {s['type']}: {s['value']}"
                        for s in team_stats.get("statistics", [])[:5]
                    ]
                    fix_summary += f"- {team_name}:\n" + "\n".join(stats_lines) + "\n"
            else:
                fix_summary += "Match Stats: Not available\n"

        # H2H
        with models.session_scope() as session:
            h2h_obj = (
                session.query(models.CachedH2H)
                .filter_by(
                    home_id=home_id,
                    away_id=away_id,
                    sport=fix["sport"],
                )
                .all()
            )
            h2h = [h.data for h in h2h_obj if h]
        if h2h:
            fix_summary += "\nLast 5 Head-to-Head:\n"
            for h in h2h:
                h_name = h["home_name"]
                a_name = h["away_name"]
                gh = h["goals"]["home"]
                ga = h["goals"]["away"]
                fix_summary += f"- {h_name} {gh} - {ga} {a_name}\n"
        else:
            fix_summary += "H2H: Not available\n"

        # LAST 5
        with models.session_scope() as session:
            last_5_home_obj = (
                session.query(models.CachedTeamResults)
                .filter_by(team_id=home_id, sport=fix["sport"])
                .first()
            )
            last_5_home = last_5_home_obj.data if last_5_home_obj else []
            last_5_away_obj = (
                session.query(models.CachedTeamResults)
                .filter_by(team_id=away_id, sport=fix["sport"])
                .first()
            )
            last_5_away = last_5_away_obj.data if last_5_away_obj else []
        fix_summary += f"\n{home_name} Last 5: {format_last_matches(matches=last_5_home, team_id=home_id, sport=fix['sport'])}\n"
        fix_summary += f"{away_name} Last 5: {format_last_matches(matches=last_5_away, team_id=away_id, sport=fix['sport'])}\n"

        summary += fix_summary + "=" * 60 + "\n"

    return summary or "No matches found."


async def generate_multimatch_coupon(fixtures_summary: str, odds: float):
    json_format = """
        {
            "matches": [
                {
                    "teams": "Team A vs Team B",
                    "sport": "...", // football, basketball, hockey or american_football
                    "tips": [
                        {
                            "risk": "Low", 
                            "market": "...", 
                            "selection": "...", 
                            "probability": 60, 
                            "odds": 1.8, 
                            "value": "✅", 
                            "reason": "..."
                        },
                        {"risk": "Medium", ...},
                        {"risk": "High", ...}
                    ]
                }
            ],
            "combo": {
                "selections": ["...","..."], 
                "combined_odds": 4.5, 
                "overall_risk": "Medium", 
                "reason": "..." 
            }
        }\n\n
    """

    odds = (
        f"{odds} total odds"
        if not isinstance(odds, list)
        else (
            f"Football total odds: {odds[0]}\n"
            f"Basketball total odds: {odds[1]}\n"
            f"American Football total odds: {odds[2]}\n"
            f"Hockey total odds: {odds[3]}\n"
        )
    )

    prompt = (
        "You are a sports betting analyst.\n\n"
        f"Based ONLY on the statistical summaries below, generate three combo bets (accumulators), each containing one selection from EVERY listed match, to reach approximately:\n"
        f"{odds}.\n\n"
        "For each combo:\n"
        "- Low Risk: Use the safest data-supported selections. If you cannot reach the requested odds with only low-risk choices, carefully increase risk (explain why).\n"
        "- Medium Risk: Moderately ambitious, but still justified by the stats.\n"
        "- High Risk: High-odds choices, always with logic from the stats.\n\n"
        "DO NOT use any matches, markets, or information outside what is provided.\n\n"
        "Matches:\n"
        f"{fixtures_summary}\n\n"
        "Return RAW JSON only in this format (no code blocks, no extra text):\n"
        f"{json_format}\n\n"
        "Then after --- send a user-friendly English markdown summary with explanations for each pick based on the stats."
    )

    resp = await openai.chat.completions.create(
        model=Config.GPT_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
    )
    content = resp.choices[0].message.content.strip()
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
    # content = resp.output_text
    if "```json" in content:
        json_part = content.split("```json")[1].split("```")[0].strip()
    else:
        json_part = content.split("---")[0].strip()
    coupon = json.loads(r"{}".format(json_part))

    md_part = ""
    if "---" in content:
        md_part = content.split("---", 1)[1].strip()
    elif "```" in content:
        after_json = content.split("`")[-1].strip()
        if after_json:
            md_part = after_json

    return coupon, md_part


async def parse_user_request(matches_text: str = None, league: str = None):
    if matches_text:
        prompt = (
            "لديك المباريات التالية:\n"
            f"'{matches_text}'\n\n"
            "المطلوب:\n"
            "استخرج أسماء المباريات بشكل موحد بالانجليزية: 'الفريق الأول vs الفريق الثاني'.\n"
            "أجب بوضوح مع قابلية تحويل الإجابة إلى json كالتالي:\n"
            """
            [
                {
                    "title": "...",
                    "sport": "..."
                }
            ]
            """
        )
    elif league:
        prompt = (
            "لديك اسم البطولة التالي:\n"
            f"'{league}'\n\n"
            "المطلوب:\n"
            "أعد كتابة اسم البطولة بشكل صحيح بالانجليزية\n"
            "أجب بوضوح مع قابلية تحويل الإجابة إلى json كالتالي:\n"
            """
            {
                "league_name": "..."
            }
            """
        )

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
    content = response.choices[0].message.content
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    result = json.loads(content)
    return result


async def gift_voucher(uid: int, s: Session, lang: models.Language):
    now = datetime.now(TIMEZONE) + timedelta(days=1)
    football_fixtures = await get_fixtures_by_sport(
        from_date=now, duration_in_days=3, sport="football"
    )
    if not football_fixtures:
        return
    fixtures = random.shuffle(
        filter_fixtures(fixtures=football_fixtures, sport="football")
    )
    fixtures = fixtures[:5]
    fixtures_summary = await summarize_fixtures_with_odds_stats(fixtures=fixtures)
    coupon_json, message_md = await generate_multimatch_coupon(
        fixtures_summary=fixtures_summary, odds=4
    )
    # Store each tip in DB
    for match_block in coupon_json["matches"]:
        label = match_block["teams"]  # e.g. "Team A vs Team B"
        fx = next(
            f
            for f in fixtures
            if label
            in [
                f"{f['home_name']} vs {f['away_name']}",
                f"{f['away_name']} vs {f['home_name']}",
            ]
        )
        for tip in match_block["tips"]:
            # إضافة التوصيات الجديدة
            recommendation = models.FixtureRecommendation(
                user_id=uid,
                fixture_id=fx["fixture_id"],
                sport=match_block["sport"],
                match_date=fx["date"],
                league_id=fx["league_id"],
                title=f"{label} → {tip['selection']}",
                market=tip["market"],
                selection=tip["selection"],
                threshold=tip.get("threshold"),
            )
            s.add(recommendation)
        s.commit()

    await TeleClientSingleton().send_message(
        entity=uid, message=TEXTS[lang]["congrats_txt"], parse_mode="md"
    )
    # Split and send final Markdown message if it's too long
    max_length = 4096  # Telegram's message length limit
    if len(message_md) <= max_length:
        await TeleClientSingleton().send_message(
            entity=uid, message=message_md, parse_mode="md"
        )
    else:
        # Split the message into parts
        parts = []
        while message_md:
            if len(message_md) > max_length:
                # Find the last newline before the limit to avoid breaking mid-line
                split_at = message_md.rfind("\n", 0, max_length)
                if split_at == -1:  # No newline found, split at max_length
                    split_at = max_length
                parts.append(message_md[:split_at])
                message_md = message_md[split_at:].lstrip()
            else:
                parts.append(message_md)
                message_md = ""

        for part in parts:
            await TeleClientSingleton().send_message(
                entity=uid, message=part, parse_mode="md"
            )


def generate_voucher_stripe_payment_link(uid: int, price: float, currency: str = "aed"):
    """
    Generate a Stripe payment link for a voucher purchase.
    """
    amount = int(price * 100)
    stripe.api_key = Config.STRIPE_API_KEY
    stripe_product_name = f"Voucher Purchase for User {uid}"
    stripe_price = stripe.Price.create(
        currency=currency,
        unit_amount=amount,
        product_data={
            "name": stripe_product_name,
        },
    )
    payment_link = stripe.PaymentLink.create(
        line_items=[
            {
                "price": stripe_price.id,
                "quantity": 1,
            }
        ],
        payment_intent_data={
            "metadata": {
                "telegram_id": str(uid),
                "type": "voucher",
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


async def check_voucher_stripe_payment_webhook(
    uid: int, price: float, currency: str = "aed"
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
                            meta = body["data"]["object"].get("metadata", {})
                            if (
                                meta.get("telegram_id") == str(uid)
                                and meta.get("type") == "voucher"
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
                                                type="voucher",
                                                amount=float(
                                                    body["data"]["object"]["amount"]
                                                )
                                                / 100,
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
                            log.error(f"Exception: {e}")
                            continue
        return False
    except Exception as e:
        log.error(f"Exception: {e}")
        return False
