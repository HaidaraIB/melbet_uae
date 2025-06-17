import sqlalchemy as sa
from models.DB import Base
from models.Language import Language
from sqlalchemy.orm import relationship
from datetime import datetime
from common.constants import TIMEZONE


class User(Base):
    __tablename__ = "users"

    user_id = sa.Column(sa.BigInteger, primary_key=True)
    username = sa.Column(sa.String)
    name = sa.Column(sa.String)
    lang = sa.Column(sa.Enum(Language), default=Language.ENGLISH)
    is_banned = sa.Column(sa.Boolean, default=0)
    is_admin = sa.Column(sa.Boolean, default=0)

    plan_code = sa.Column(sa.String, sa.ForeignKey("plans.code"))
    plan = relationship("Plan", back_populates="users")

    trial_used = sa.Column(sa.Boolean, default=False)

    # Relationships (one-to-many)
    sessions = relationship("UserSession", back_populates="user")
    player_accounts = relationship("PlayerAccount", back_populates="user")
    recommendations = relationship("FixtureRecommendation", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

    # Relationship for fraud logs (both as user and copied_from)
    fraud_committed = relationship(
        "FraudLog",
        foreign_keys="[FraudLog.user_id]",
        back_populates="user",
    )
    fraud_copied_from = relationship(
        "FraudLog",
        foreign_keys="[FraudLog.copied_from_id]",
        back_populates="copied_from_user",
    )

    def __repr__(self):
        return f"User(user_id={self.user_id}, username={self.username}, name={self.name}, is_admin={bool(self.is_admin)}, is_banned={bool(self.is_banned)}"


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.user_id"))
    plan_code = sa.Column(sa.String, sa.ForeignKey("plans.code"))
    multiplier = sa.Column(sa.Float, nullable=True)  # لإدارة رأس المال فقط
    days = sa.Column(sa.Integer, nullable=True)  # لإدارة رأس المال فقط
    price = sa.Column(sa.String)  # necessary for capital management
    remaining_vouchers = sa.Column(sa.Integer)
    status = sa.Column(sa.String, default="active")  # active / expired / canceled...
    created_at = sa.Column(sa.DateTime, default=datetime.now(TIMEZONE))

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
