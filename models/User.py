import sqlalchemy as sa
from models.DB import Base
from models.Language import Language
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    user_id = sa.Column(sa.BigInteger, primary_key=True)
    username = sa.Column(sa.String)
    name = sa.Column(sa.String)
    lang = sa.Column(sa.Enum(Language), default=Language.ARABIC)
    is_banned = sa.Column(sa.Boolean, default=0)
    is_admin = sa.Column(sa.Boolean, default=0)

    # Relationships (one-to-many)
    sessions = relationship("UserSession", back_populates="user")
    messages = relationship("SessionMessage", back_populates="user")
    payment_texts = relationship("PaymentText", back_populates="user")
    melbet_account = relationship("MelbetAccount", back_populates="user", uselist=False)
    account_changes = relationship("MelbetAccountChange", back_populates="user")
    recommendations = relationship("FixtureRecommendation", back_populates="user")

    # Relationship for fraud logs (both as user and copied_from)
    fraud_committed = relationship(
        "FraudLog", foreign_keys="[FraudLog.user_id]", back_populates="user"
    )
    fraud_copied_from = relationship(
        "FraudLog",
        foreign_keys="[FraudLog.copied_from_id]",
        back_populates="copied_from_user",
    )

    def __repr__(self):
        return f"User(user_id={self.user_id}, username={self.username}, name={self.name}, is_admin={bool(self.is_admin)}, is_banned={bool(self.is_banned)}"
