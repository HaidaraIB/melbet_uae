import sqlalchemy as sa
from datetime import datetime
from common.constants import TIMEZONE
from sqlalchemy.orm import relationship, Session
from models.DB import Base
from models.Language import Language
from models.PlayerAccount import PlayerAccount


class Proof(Base):
    __tablename__ = "proofs"
    transaction_id = sa.Column(
        sa.Integer, sa.ForeignKey("transactions.id"), primary_key=True
    )
    photo_data = sa.Column(sa.LargeBinary)

    transaction = relationship("Transaction", back_populates="proof")


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
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
        account_number,
        status,
        date

    Withdraw:
        user_id,
        payment_method_id,
        type,
        withdrawal_code,
        payment_info,
        account_number,
        status

    """

    __tablename__ = "transactions"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
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
        sa.Enum("deposit", "withdraw", "offer", name="transaction_type"), nullable=False
    )
    amount = sa.Column(sa.Float, nullable=True)
    tax = sa.Column(sa.Float, nullable=True)
    currency = sa.Column(sa.String(3), nullable=True)

    mobi_operation_id = sa.Column(sa.String, nullable=True)

    receipt_id = sa.Column(sa.String, unique=True, nullable=True)
    withdrawal_code = sa.Column(sa.String(32), unique=True, nullable=True)
    payment_info = sa.Column(sa.Text, nullable=True)

    account_number = sa.Column(
        sa.String, sa.ForeignKey("player_accounts.account_number"), nullable=False
    )

    # Status and timestamps
    status = sa.Column(
        sa.Enum("pending", "approved", "failed", "declined", name="transaction_status"),
        default="pending",
        index=True,
    )
    description = sa.Column(sa.TEXT, nullable=True)
    date = sa.Column(sa.DateTime, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.now(TIMEZONE), index=True)
    completed_at = sa.Column(sa.DateTime, nullable=True)
    decline_reason = sa.Column(sa.TEXT, nullable=True)
    fail_reason = sa.Column(sa.TEXT, nullable=True)

    # Relationships
    payment_method = relationship("PaymentMethod", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
    proof = relationship("Proof", back_populates="transaction")
    receipt = relationship("Receipt", back_populates="transaction", uselist=False)
    player_account = relationship("PlayerAccount", back_populates="transactions")

    @classmethod
    def add_offer_transaction(cls, s: Session, player_account: PlayerAccount):
        offer_tx = Transaction(
            account_number=player_account.account_number,
            user_id=player_account.user_id,
            type="offer",
            amount=player_account.offer_prize,
            currency=player_account.currency,
            description="Reward for completing welcome offer",
        )
        s.add(offer_tx)
        s.commit()
        return offer_tx

    def stringify(self, lang: Language):
        if lang == Language.ENGLISH.name:
            base_str = (
                f"Transaction ID: <code>{self.id}</code>\n"
                f"Amount: <code>{self.amount:.2f}</code> {self.currency}\n"
                f"Payment Method: <b>{self.payment_method.name}</b>\n"
                f"Account: <code>{self.account_number}</code>\n"
                f"Status: {self.status}"
            )

            if self.type == "deposit":
                return (
                    base_str + f"\nDate: {self.created_at.strftime('%Y-%m-%d %H:%M')}"
                )
            else:
                return (
                    base_str + f"\nWithdrawal Code: <code>{self.withdrawal_code}</code>"
                )
        else:
            base_str = (
                f"رقم المعاملة: <code>{self.id}</code>\n"
                f"المبلغ: <code>{self.amount:.2f}</code> {self.currency}\n"
                f"وسيلة الدفع: <b>{self.payment_method.name}</b>\n"
                f"رقم الحساب: <code>{self.account_number}</code>\n"
                f"الحالة: {self.status}\n"
            )

            if self.type == "deposit":
                return (
                    base_str + f"التاريخ:\n{self.created_at.strftime('%Y-%m-%d %H:%M')}"
                )
            else:
                return base_str + f"كود السحب: <code>{self.withdrawal_code}</code>"

    def __str__(self):
        base_str = (
            f"New {self.type.capitalize()} request from @{self.user.username}:\n"
            f"Amount: <code>{self.amount:.2f}</code> {self.currency}\n"
            f"Payment Method: <b>{self.payment_method.name}</b>\n"
            f"Account: <code>{self.account_number}</code>\n"
            f"Status: {self.status}\n"
        )

        if self.type == "deposit":
            return base_str + (
                f"Receipt ID: <code>{self.receipt_id}</code>\n"
                f"Date: {self.created_at.strftime('%Y-%m-%d %H:%M')}"
            )
        else:
            return base_str + (
                f"Withdrawal Code: <code>{self.withdrawal_code}</code>\n"
                f"Payment Info: {self.payment_info}"
            )


class Receipt(Base):
    __tablename__ = "receipts"

    id = sa.Column(sa.String, primary_key=True)
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
