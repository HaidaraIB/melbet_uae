from models.DB import Base
import sqlalchemy as sa
from sqlalchemy.orm import relationship


class MelbetAccount(Base):
    __tablename__ = "melbet_accounts"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.user_id"), unique=True)
    account_number = sa.Column(sa.String, nullable=False)
    username = sa.Column(sa.String)
    timestamp = sa.Column(sa.DateTime)

    user = relationship("User", back_populates="melbet_account")
