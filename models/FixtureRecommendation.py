import sqlalchemy as sa
from sqlalchemy.orm import relationship
from models.DB import Base


class FixtureRecommendation(Base):
    __tablename__ = "fixture_recommendations"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.user_id"), nullable=False)
    fixture_id = sa.Column(sa.Integer, nullable=False)
    match_date = sa.Column(sa.String, nullable=False)
    league_id = sa.Column(sa.Integer, nullable=False)
    title = sa.Column(sa.String, nullable=False)
    market = sa.Column(sa.String, nullable=False)
    selection = sa.Column(sa.String, nullable=False)
    threshold = sa.Column(sa.String, nullable=True)

    user = relationship("User", back_populates="recommendations")
