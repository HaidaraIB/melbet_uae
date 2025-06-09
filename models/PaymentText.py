import sqlalchemy as sa
from models.DB import Base
from sqlalchemy.orm import relationship


class PaymentText(Base):
    __tablename__ = "payment_texts"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.user_id"))
    session_type = sa.Column(sa.String)
    text = sa.Column(sa.Text)
    transaction_id = sa.Column(sa.String, unique=True)
    timestamp = sa.Column(sa.DateTime)

    user = relationship("User", back_populates="payment_texts")
