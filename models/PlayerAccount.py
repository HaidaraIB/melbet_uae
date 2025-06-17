from models.DB import Base
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from common.common import format_datetime


class PlayerAccount(Base):
    __tablename__ = "player_accounts"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.user_id"))
    account_number = sa.Column(sa.String, nullable=False, unique=True)
    country = sa.Column(sa.String, nullable=False, default="United Arab Emirates")
    currency = sa.Column(sa.String, default="aed")
    is_points = sa.Column(sa.Boolean, default=False)
    registration_date = sa.Column(sa.DateTime)

    user = relationship("User", back_populates="player_account")
    transactions = relationship("Transaction", back_populates="player_account")

    def __str__(self):
        return (
            f"رقم الحساب: <code>{self.account_number}</code>\n"
            f"معرف التيليجرام: <code>{self.user_id}</code>\n"
        )
