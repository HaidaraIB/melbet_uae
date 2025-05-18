import sqlalchemy as sa
from models.DB import Base

class RecommendationHistory(Base):
    __tablename__ = 'recommendation_history'
    
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    user_id = sa.Column(sa.Integer)
    fixture_id = sa.Column(sa.Integer)
    used = sa.Column(sa.String)
    success = sa.Column(sa.Integer)
    date = sa.Column(sa.String)
    