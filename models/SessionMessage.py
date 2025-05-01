import sqlalchemy as sa
from models.DB import Base
from sqlalchemy.orm import relationship


class SessionMessage(Base):
    __tablename__ = "session_messages"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.user_id"))
    session_type = sa.Column(sa.String)
    role = sa.Column(sa.String)
    message = sa.Column(sa.Text)
    timestamp = sa.Column(sa.DateTime)

    user = relationship("User", back_populates="messages")
