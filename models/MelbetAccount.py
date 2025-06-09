from models.DB import Base
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from common.common import format_datetime

class MelbetAccount(Base):
    __tablename__ = "melbet_accounts"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.user_id"), unique=True)
    account_number = sa.Column(sa.String, nullable=False)
    timestamp = sa.Column(sa.DateTime)

    user = relationship("User", back_populates="melbet_account")


    def __str__(self):
        return (
            f"رقم الحساب: <code>{self.account_number}</code>\n"
            f"معرف التيليجرام: <code>{self.user_id}</code>\n"
            f"تاريخ الطلب:\n{format_datetime(self.timestamp)}\n"
        )