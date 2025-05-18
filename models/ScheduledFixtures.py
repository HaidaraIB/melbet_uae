import sqlalchemy as sa
from models.DB import Base

class ScheduledFixtures(Base):
    __tablename__ = 'scheduled_fixtures'
    
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    fixture_id = sa.Column(sa.Integer)
    user_id = sa.Column(sa.Integer)
    match_date = sa.Column(sa.String)
    recommendations = sa.Column(sa.Text)
    