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
    created_at = sa.Column(sa.DateTime, default=datetime.now(TIMEZONE))

    payment_method = relationship("PaymentMethod", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
