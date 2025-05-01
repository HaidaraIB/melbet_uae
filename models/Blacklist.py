from sqlalchemy import Column, Integer, String, DateTime
from models.DB import Base


class Blacklist(Base):
    __tablename__ = "blacklist"

    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    timestamp = Column(DateTime)
