import sqlalchemy as sa
from models.DB import Base
from datetime import datetime
from common.constants import TIMEZONE
from sqlalchemy.orm import relationship


class Proof(Base):
    __tablename__ = "proofs"
    transaction_id = sa.Column(
        sa.Integer, sa.ForeignKey("transactions.id"), primary_key=True
    )
    photo_data = sa.Column(sa.LargeBinary)

    transaction = relationship("Transaction", back_populates="proof")


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(
        sa.String, unique=True, nullable=False
    )  # e.g., "Bank Transfer", "Crypto USDT"
    details = sa.Column(
        sa.Text, nullable=False
    )  # Instructions for the user, e.g., "Bank Name: ..., Account: ..."
    type = sa.Column(sa.String, default="both")  # 'deposit' or 'withdrawal' or 'both'
    is_active = sa.Column(sa.Boolean, default=True)  # To enable/disable the method
    mode = sa.Column(sa.String, default="manual")

    transactions = relationship("Transaction", back_populates="payment_method")
    receipts = relationship("Receipt", back_populates="payment_method")

    def __str__(self):
        return self.name


class Transaction(Base):
    """
    Deposit:
        user_id,
        payment_method_id,
        type,
        amount,
        currency,
        receipt_id,
        player_account,
        status,
        date,
        timestamp

    Withdraw:
        user_id,
        payment_method_id,
        type,
        withdrawal_code,
        payment_info,
        player_account,
        status,
        timestamp

    """

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
    currency = sa.Column(sa.String)
    payment_info = sa.Column(sa.String, nullable=True)
    withdrawal_code = sa.Column(sa.String, nullable=True)

    receipt_id = sa.Column(sa.String, unique=True, index=True, nullable=True)
    player_account = sa.Column(sa.String, nullable=True)

    status = sa.Column(sa.String, default="pending", index=True)
    date = sa.Column(sa.DateTime, nullable=True)
    timestamp = sa.Column(sa.DateTime, default=datetime.now(TIMEZONE))
    decline_reason = sa.Column(sa.String)

    payment_method = relationship("PaymentMethod", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
    proof = relationship("Proof", back_populates="transaction")
    receipt = relationship("Receipt", back_populates="transaction", uselist=False)

    def __str__(self):
        if self.type == "deposit":
            return (
                f"New Deposit request from @{self.user.username}:\n"
                f"Amount: <code>{self.amount}</code> {self.currency or ""}\n"
                f"Transaction ID: <code>{self.receipt_id}</code>\n"
                f"Payment Method: <b>{self.payment_method.name}</b>\n"
                f"Date: {self.date or "N/A"}\n"
                f"Account Number: <code>{self.player_account}</code>"
            )
        else:
            return (
                f"New Withdrawal request from @{self.user.username}:\n"
                f"Withdrawal Code: <code>{self.withdrawal_code}</code>\n"
                f"Payment Method: <b>{self.payment_method.name}</b>\n"
                f"Payment Info: {self.payment_info}\n"
                f"Account Number: <code>{self.player_account}</code>"
            )


class Receipt(Base):
    __tablename__ = "receipts"

    id = sa.Column(sa.String, primary_key=True)
    user_id = sa.Column(sa.Integer, nullable=True)
    amount = sa.Column(sa.Float, nullable=True)
    payment_method_id = sa.Column(sa.Integer, sa.ForeignKey("payment_methods.id"))
    transaction_id = sa.Column(sa.Integer, sa.ForeignKey("transactions.id"))

    available_balance_at_the_time = sa.Column(sa.Float, nullable=True)
    timestamp = sa.Column(sa.DateTime, default=datetime.now(TIMEZONE))

    transaction = relationship("Transaction", back_populates="receipt", uselist=False)
    payment_method = relationship("PaymentMethod", back_populates="receipts")
