import sqlalchemy as sa
from models.DB import Base
from datetime import datetime
from common.constants import TIMEZONE


class GroupSubscription(Base):
    __tablename__ = "group_subscriptions"

    id = sa.Column(sa.Integer, primary_key=True)
    group_id = sa.Column(sa.BigInteger, unique=True, index=True)
    is_active = sa.Column(sa.Boolean, default=False)
    expire_date = sa.Column(sa.DateTime(timezone=True), nullable=True)
    plan_code = sa.Column(sa.String, default="default")
    status = sa.Column(sa.String, default="active")  # active / expired / canceled...
    created_at = sa.Column(sa.DateTime(timezone=True), default=datetime.now(TIMEZONE))
    admin_id = sa.Column(sa.BigInteger, nullable=False)
