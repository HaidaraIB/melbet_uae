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
        date

    Withdraw:
        user_id,
        payment_method_id,
        type,
        withdrawal_code,
        payment_info,
        player_account,
        status

    """

    __tablename__ = "transactions"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("users.user_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    payment_method_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("payment_methods.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Transaction type and amount details
    type = sa.Column(
        sa.Enum("deposit", "withdraw", name="transaction_type"), nullable=False
    )
    amount = sa.Column(sa.Float, nullable=False)
    currency = sa.Column(sa.String(3), nullable=False)

    receipt_id = sa.Column(sa.String, unique=True, nullable=True)
    withdrawal_code = sa.Column(sa.String(32), unique=True, nullable=True)
    payment_info = sa.Column(sa.Text, nullable=True)
    player_account = sa.Column(sa.String(64), nullable=False)

    # Status and timestamps
    status = sa.Column(
        sa.Enum("pending", "approved", "failed", "declined", name="transaction_status"),
        default="pending",
        index=True,
    )
    created_at = sa.Column(sa.DateTime, default=datetime.now(TIMEZONE), index=True)
    updated_at = sa.Column(
        sa.DateTime, default=datetime.now(TIMEZONE), onupdate=datetime.now(TIMEZONE)
    )
    completed_at = sa.Column(sa.DateTime, nullable=True)
    decline_reason = sa.Column(sa.String(255), nullable=True)

    # Relationships
    payment_method = relationship("PaymentMethod", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
    proof = relationship("Proof", back_populates="transaction")
    receipt = relationship("Receipt", back_populates="transaction", uselist=False)

    def __str__(self):
        base_str = (
            f"New {self.type.capitalize()} request from @{self.user.username}:\n"
            f"Amount: <code>{self.amount:.2f}</code> {self.currency}\n"
            f"Payment Method: <b>{self.payment_method.name}</b>\n"
            f"Account: <code>{self.player_account}</code>\n"
            f"Status: {self.status}"
        )

        if self.type == "deposit":
            return base_str + f"\nDate: {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        else:
            return base_str + f"\nWithdrawal Code: <code>{self.withdrawal_code}</code>"


class Receipt(Base):
    __tablename__ = "receipts"

    id = sa.Column(sa.String, primary_key=True)  # Using UUID
    amount = sa.Column(sa.Float, nullable=False)
    payment_method_id = sa.Column(
        sa.Integer, sa.ForeignKey("payment_methods.id", ondelete="SET NULL")
    )

    # Financial details
    available_balance_at_the_time = sa.Column(sa.Float, nullable=False)

    # Timestamps
    issued_at = sa.Column(sa.DateTime, default=datetime.now(TIMEZONE), index=True)

    # Make transaction_id nullable for initial creation
    transaction_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("transactions.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )

    # Relationship with uselist=False for one-to-one
    transaction = relationship("Transaction", back_populates="receipt", uselist=False)
    payment_method = relationship("PaymentMethod", back_populates="receipts")
