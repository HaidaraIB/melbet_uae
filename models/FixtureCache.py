import sqlalchemy as sa
from sqlalchemy.orm import relationship
from models.DB import Base


class CachedFixture(Base):
    __tablename__ = "cached_fixtures"

    id = sa.Column(sa.Integer, primary_key=True)
    fixture_id = sa.Column(sa.Integer, unique=True)
    league_id = sa.Column(sa.Integer)
    season = sa.Column(sa.Integer)
    fixture_date = sa.Column(sa.DateTime)
    data = sa.Column(sa.JSON)  # Stores the full fixture data
    sport = sa.Column(sa.String)

    # Relationships to other cached data
    odds = relationship("CachedOdds", back_populates="fixture")
    stats = relationship("CachedFixtureStats", back_populates="fixture")
    h2h = relationship("CachedH2H", back_populates="fixture")
    standings = relationship("CachedStandings", back_populates="fixture")
    team_stats = relationship("CachedTeamStats", back_populates="fixture")


class CachedOdds(Base):
    __tablename__ = "cached_odds"

    id = sa.Column(sa.Integer, primary_key=True)
    fixture_id = sa.Column(sa.Integer, sa.ForeignKey("cached_fixtures.fixture_id"))
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String)

    fixture = relationship("CachedFixture", back_populates="odds")


class CachedFixtureStats(Base):
    __tablename__ = "cached_fixture_stats"

    id = sa.Column(sa.Integer, primary_key=True)
    fixture_id = sa.Column(sa.Integer, sa.ForeignKey("cached_fixtures.fixture_id"))
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)

    fixture = relationship("CachedFixture", back_populates="stats")


class CachedH2H(Base):
    __tablename__ = "cached_h2h"

    id = sa.Column(sa.Integer, primary_key=True)
    fixture_id = sa.Column(sa.Integer, sa.ForeignKey("cached_fixtures.fixture_id"))
    home_id = sa.Column(sa.Integer)
    away_id = sa.Column(sa.Integer)
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String)

    fixture = relationship("CachedFixture", back_populates="h2h")


class CachedStandings(Base):
    __tablename__ = "cached_standings"

    id = sa.Column(sa.Integer, primary_key=True)
    fixture_id = sa.Column(sa.Integer, sa.ForeignKey("cached_fixtures.fixture_id"))
    league_id = sa.Column(sa.Integer)
    team_id = sa.Column(sa.Integer)
    season = sa.Column(sa.Integer)
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String)

    fixture = relationship("CachedFixture", back_populates="standings")


class CachedTeamStats(Base):
    __tablename__ = "cached_team_stats"

    id = sa.Column(sa.Integer, primary_key=True)
    fixture_id = sa.Column(sa.Integer, sa.ForeignKey("cached_fixtures.fixture_id"))
    team_id = sa.Column(sa.Integer)
    league_id = sa.Column(sa.Integer)
    season = sa.Column(sa.Integer)
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String)

    fixture = relationship("CachedFixture", back_populates="team_stats")


class CachedTeamResults(Base):
    __tablename__ = "cached_team_results"

    id = sa.Column(sa.Integer, primary_key=True)
    team_id = sa.Column(sa.Integer, index=True)
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String)

    # Index for faster lookups
    __table_args__ = (sa.Index("idx_team_results_team_id", "team_id"),)
