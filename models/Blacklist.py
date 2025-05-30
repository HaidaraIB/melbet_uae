import sqlalchemy as sa
from models.DB import Base


class Blacklist(Base):
    __tablename__ = "blacklist"

    user_id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String)
    timestamp = sa.Column(sa.DateTime)
