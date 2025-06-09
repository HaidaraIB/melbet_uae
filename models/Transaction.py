import sqlalchemy as sa
from models.DB import Base
from datetime import datetime
from common.constants import TIMEZONE
from sqlalchemy.orm import relationship


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(
        sa.String, unique=True, nullable=False
    )  # e.g., "Bank Transfer", "Crypto USDT"
    details = sa.Column(
        sa.Text, nullable=False
    )  # Instructions for the user, e.g., "Bank Name: ..., Account: ..."
    type = sa.Column(sa.String, default="deposit")  # 'deposit' or 'withdrawal'
    is_active = sa.Column(sa.Boolean, default=True)  # To enable/disable the method

    transactions = relationship("Transaction", back_populates="payment_method")

    def __str__(self):
        return self.name


class Transaction(Base):
    __tablename__ = "transactions"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("users.user_id"),
        index=True,
        nullable=False,
    )

    payment_method_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("payment_methods.id"),
        nullable=True,
    )

    type = sa.Column(sa.String, nullable=False)  # 'deposit' or 'withdraw'
    amount = sa.Column(sa.String, nullable=True)

    receipt_id = sa.Column(sa.String, unique=True, index=True, nullable=True)
    player_account = sa.Column(sa.String, nullable=True)

    status = sa.Column(sa.String, default="pending", index=True)
    date = sa.Column(sa.DateTime, nullable=True)
    timestamp = sa.Column(sa.DateTime, default=datetime.now(TIMEZONE))

    payment_method = relationship("PaymentMethod", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
    fraud_logs = relationship("FraudLog", back_populates="transaction")

    def __str__(self):
        return (
            f"New {self.type} request from @{self.user.username}:\n"
            f"Amount: <code>{self.amount}</code>\n"
            f"Transaction ID: <code>{self.receipt_id}</code>\n"
            f"Payment Method: <b>{self.payment_method.name}</b>\n"
            f"Date: {self.date or "N/A"}\n"
            f"Account Number: <code>{self.player_account}</code>"
        )
