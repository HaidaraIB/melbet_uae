import sqlalchemy as sa
from sqlalchemy.orm import relationship
from models.DB import Base


class FraudLog(Base):
    __tablename__ = "fraud_logs"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.user_id"))
    username = sa.Column(sa.String, nullable=False)
    copied_from_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.user_id"))
    copied_from_username = sa.Column(sa.String)
    timestamp = sa.Column(sa.DateTime)
    receipt_text = sa.Column(sa.Text, nullable=False)
    transaction_id = sa.Column(sa.String)

    user = relationship(
        "User", foreign_keys=[user_id], back_populates="fraud_committed"
    )
    copied_from_user = relationship(
        "User", foreign_keys=[copied_from_id], back_populates="fraud_copied_from"
    )
