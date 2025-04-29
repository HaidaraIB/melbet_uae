import sqlalchemy as sa
from models.DB import Base
from models.Language import Language


class User(Base):
    __tablename__ = "users"

    user_id = sa.Column(sa.BigInteger, primary_key=True)
    username = sa.Column(sa.String)
    name = sa.Column(sa.String)
    lang = sa.Column(sa.Enum(Language), default=Language.ARABIC)
    is_banned = sa.Column(sa.Boolean, default=0)
    is_admin = sa.Column(sa.Boolean, default=0)

    def __repr__(self):
        return f"User(user_id={self.user_id}, username={self.username}, name={self.name}, is_admin={bool(self.is_admin)}, is_banned={bool(self.is_banned)}"
