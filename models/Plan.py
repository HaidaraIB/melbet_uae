import sqlalchemy as sa
from models.DB import Base, session_scope
from sqlalchemy.orm import relationship

PLANS = {
    "basic": {
        "name_en": "Basic Plan",
        "name_ar": "خطة أساسية",
        "price": 50,
        "details_en": "Includes daily tips for selected matches with simplified statistical analysis. Suitable for beginners or those seeking the safest betting opportunities.",
        "details_ar": "تتضمن توصيات يومية لمباريات مختارة مع تحليل إحصائي مبسط. مناسبة للمبتدئين أو من يرغب بمتابعة فرص الرهان الأكثر أماناً.",
        "max_odds": 10,
    },
    "plus": {
        "name_en": "Plus Plan",
        "name_ar": "خطة بلس",
        "price": 120,
        "details_en": "All Basic features + exclusive tips for advanced markets, instant notifications, priority support, and extended analytical summaries for each match.",
        "details_ar": "تتضمن كل ميزات الخطة الأساسية + توصيات حصرية لأسواق متقدمة، إشعارات مباشرة، دعم فني أسرع، وملخص تحليلي موسّع لكل مباراة.",
        "max_odds": 25,
    },
    "pro": {
        "name_en": "Pro Plan",
        "name_ar": "خطة برو",
        "price": 250,
        "details_en": "Elite professional service: multi-market tips, direct expert supervision, personalized strategies, and detailed weekly reports.",
        "details_ar": "خدمة احترافية للنخبة تشمل: توصيات متعددة الأسواق، إشراف مباشر من خبراء، استراتيجيات مخصصة حسب رغبتك، مع تقارير أسبوعية مفصلة.",
        "max_odds": 50,
    },
    "capital_management": {
        "name_en": "Capital Management",
        "name_ar": "إدارة رأس المال",
        "price": 0,
        "details_en": "Special service for professional bankroll management and growth. Choose your target multiplier and duration to get a tailored price.",
        "details_ar": "خدمة خاصة لإدارة رأس المال ومضاعفته باحترافية وفق أهدافك (حدد المضاعفة والمدة المطلوبة لمعرفة السعر).",
        "max_odds": 0,
    },
}


class Plan(Base):
    __tablename__ = "plans"
    id = sa.Column(sa.Integer, primary_key=True)
    code = sa.Column(sa.String, unique=True)  # basic, plus, pro, capital_management
    name_ar = sa.Column(sa.String)
    name_en = sa.Column(sa.String)
    price = sa.Column(sa.Float)
    max_odds = sa.Column(sa.Integer)
    vouchers = sa.Column(sa.Integer, default=30)
    duration = sa.Column(sa.Integer, default=30)
    details_ar = sa.Column(sa.String)
    details_en = sa.Column(sa.String)

    subscriptions = relationship("Subscription", back_populates="plan")
    users = relationship("User", back_populates="plan")

    @classmethod
    def initialize(cls):
        with session_scope() as s:
            for code, plan in PLANS.items():
                p = s.query(Plan).filter_by(code=code).first()
                if p:
                    continue
                s.add(
                    Plan(
                        code=code,
                        name_ar=plan["name_ar"],
                        name_en=plan["name_en"],
                        price=plan["price"],
                        details_ar=plan["details_ar"],
                        details_en=plan["details_en"],
                        max_odds=plan["max_odds"],
                    )
                )
                s.commit()
