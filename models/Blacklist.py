import sqlalchemy as sa
from models.DB import Base
from sqlalchemy.orm import relationship


class Blacklist(Base):
    __tablename__ = "blacklist"

    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.user_id"), primary_key=True)
    timestamp = sa.Column(sa.DateTime)

    user = relationship("User")
