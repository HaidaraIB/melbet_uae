from telegram import InlineKeyboardButton
from models import Language

PLANS = {
    Language.ARABIC: {
        "basic": {
            "name": "خطة أساسية",
            "price": "٩٩ ر.س/شهر",
            "details": "الوصول إلى الأدوات الأساسية، تقارير أسبوعية، دعم عبر البريد الإلكتروني",
        },
        "plus": {
            "name": "خطة بلس",
            "price": "١٩٩ ر.س/شهر",
            "details": "كل مميزات الخطة الأساسية بالإضافة إلى تحليلات متقدمة، تقارير يومية، دعم سريع",
        },
        "pro": {
            "name": "خطة برو",
            "price": "٣٩٩ ر.س/شهر",
            "details": "كل مميزات خطة بلس بالإضافة إلى جلسات استشارية، تحليلات مخصصة، دعم على مدار الساعة",
        },
        "capital_management": {
            "name": "إدارة رأس المال",
            "price": "يبدأ من ١٠٠٠ ر.س/شهر",
            "details": "حلول إدارة رأس المال المخصصة، تحليلات شاملة، فريق دعم مخصص",
        },
    },
    Language.ENGLISH: {
        "basic": {
            "name": "Basic Plan",
            "price": "$29/month",
            "details": "Access to basic tools, weekly reports, email support",
        },
        "plus": {
            "name": "Plus Plan",
            "price": "$59/month",
            "details": "All Basic features plus advanced analytics, daily reports, priority support",
        },
        "pro": {
            "name": "Pro Plan",
            "price": "$129/month",
            "details": "All Plus features plus 1-on-1 consultations, custom analytics, 24/7 support",
        },
        "capital_management": {
            "name": "Capital Management",
            "price": "Starting from $499/month",
            "details": "Custom capital management solutions, comprehensive analytics, dedicated account manager",
        },
    },
}


def build_plans_keyboard(lang):
    return [
        [
            InlineKeyboardButton(
                text=plan["name"],
                callback_data=plan_code,
            )
        ]
        for plan_code, plan in PLANS[lang].items()
    ]
