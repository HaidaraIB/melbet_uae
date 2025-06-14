from models.DB import Base
import sqlalchemy as sa
from sqlalchemy.orm import relationship


class PlayerAccountChange(Base):
    __tablename__ = "player_account_changes"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.user_id"))
    username = sa.Column(sa.String)
    old_account = sa.Column(sa.String)
    new_account = sa.Column(sa.String)
    timestamp = sa.Column(sa.DateTime)

    user = relationship("User", back_populates="account_changes")
