from models.DB import Base
import sqlalchemy as sa
from sqlalchemy.orm import relationship, Session
from models.Transaction import Transaction
from datetime import datetime


class PlayerAccount(Base):
    __tablename__ = "player_accounts"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.user_id"))
    account_number = sa.Column(sa.String, nullable=False, unique=True)
    country = sa.Column(sa.String, nullable=False, default="uae")
    currency = sa.Column(sa.String, default="aed")
    is_points = sa.Column(sa.Boolean, default=False)
    registration_date = sa.Column(sa.DateTime)

    offer_start_date = sa.Column(sa.DateTime)
    offer_expiry_date = sa.Column(sa.DateTime)
    offer_completed = sa.Column(sa.Boolean, default=False)
    offer_prize = sa.Column(sa.Float)

    user = relationship("User", back_populates="player_accounts")
    transactions = relationship("Transaction", back_populates="player_account")

    def check_offer_progress(self, s: Session):
        now = datetime.now()
        if self.offer_completed or now >= self.offer_expiry_date:
            return {}

        deposits = (
            s.query(Transaction)
            .filter(
                Transaction.account_number == self.account_number,
                Transaction.type == "deposit",
                Transaction.status == "approved",
                Transaction.created_at >= self.offer_start_date,
                Transaction.created_at <= self.offer_expiry_date,
                Transaction.currency == self.currency,
            )
            .order_by(Transaction.created_at.asc())
            .all()
        )

        min_total = 200 if self.currency == "aed" else 400_000

        days_done = set([d.created_at.date() for d in deposits])
        num_days = len(days_done)
        total_amount = sum(d.amount for d in deposits)

        deposit_days_left = max(7 - num_days, 0)
        amount_left = max(min_total - total_amount, 0)

        completed = (deposit_days_left == 0) and (amount_left == 0)

        return {
            "num_days": num_days,
            "total_amount": total_amount,
            "deposit_days_left": deposit_days_left,
            "amount_left": amount_left,
            "completed": completed,
        }

    def __str__(self):
        return (
            f"رقم الحساب: <code>{self.account_number}</code>\n"
            f"معرف التيليجرام: <code>{self.user_id}</code>\n"
        )
