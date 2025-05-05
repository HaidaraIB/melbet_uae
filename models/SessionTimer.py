import sqlalchemy as sa
from models.DB import Base
from datetime import datetime


class SessionTimer(Base):
    __tablename__ = "session_timers"

    uid = sa.Column(sa.Integer, primary_key=True)
    gid = sa.Column(sa.Integer, primary_key=True)
    end_time = sa.Column(sa.Integer)

    def __repr__(self):
        return f"SessionTimer({self.uid}, {self.gid}, {datetime.fromtimestamp(self.end_time)})"
