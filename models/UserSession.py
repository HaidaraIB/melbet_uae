from models.DB import Base
from sqlalchemy.orm import relationship
import sqlalchemy as sa


class UserSession(Base):
    __tablename__ = "user_sessions"

    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.user_id"), primary_key=True)
    group_id = sa.Column(sa.BigInteger, nullable=False)
    session_type = sa.Column(sa.String, nullable=False)
    last_active = sa.Column(sa.DateTime, nullable=False)
    created_at = sa.Column(sa.DateTime, nullable=False)

    user = relationship("User", back_populates="sessions")
