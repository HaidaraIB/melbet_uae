import sqlalchemy as sa
from models.DB import Base


class Setting(Base):
    __tablename__ = "settings"

    key = sa.Column(sa.String, primary_key=True)
    value = sa.Column(sa.String)
