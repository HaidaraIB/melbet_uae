from telegram import InlineKeyboardButton
from models import Language

PLANS = {
    Language.ARABIC: {
        "basic": {"name": "خطة أساسية"},
        "plus": {"name": "خطة بلس"},
        "pro": {"name": "خطة برو"},
        "capital_management": {"name": "إدارة رأس المال"},
    },
    Language.ENGLISH: {
        "basic": {"name": "Basic Plan"},
        "plus": {"name": "Plus Plan"},
        "pro": {"name": "Pro Plan"},
        "capital_management": {"name": "Capital Management"},
    },
}


def build_plans_keyboard(lang):
    return [
        [
            InlineKeyboardButton(
                text=plan['name'],
                callback_data=plan_code,
            )
        ]
        for plan_code, plan in PLANS[lang].items()
    ]
