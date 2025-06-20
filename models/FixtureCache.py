import sqlalchemy as sa
from sqlalchemy.orm import relationship
from models.DB import Base


class CachedFixture(Base):
    __tablename__ = "cached_fixtures"

    id = sa.Column(sa.Integer, primary_key=True)
    fixture_id = sa.Column(sa.Integer)
    league_id = sa.Column(sa.Integer)
    season = sa.Column(sa.Integer)
    fixture_date = sa.Column(sa.DateTime)
    data = sa.Column(sa.JSON)
    sport = sa.Column(sa.String)

    __table_args__ = (
        sa.UniqueConstraint("fixture_id", "sport", name="_fixture_id_sport_uc"),
    )

    # Relationships to other cached data
    odds = relationship("CachedOdds", back_populates="fixture")
    stats = relationship("CachedFixtureStats", back_populates="fixture")


class CachedOdds(Base):
    __tablename__ = "cached_odds"

    id = sa.Column(sa.Integer, primary_key=True)
    fixture_id = sa.Column(sa.Integer)
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String)

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["fixture_id", "sport"],
            ["cached_fixtures.fixture_id", "cached_fixtures.sport"],
        ),
    )

    fixture = relationship("CachedFixture", back_populates="odds")


class CachedFixtureStats(Base):
    __tablename__ = "cached_fixture_stats"

    id = sa.Column(sa.Integer, primary_key=True)
    fixture_id = sa.Column(sa.Integer)
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)

    sport = sa.Column(sa.String)

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["fixture_id", "sport"],
            ["cached_fixtures.fixture_id", "cached_fixtures.sport"],
        ),
    )

    fixture = relationship("CachedFixture", back_populates="stats")


class CachedInjuries(Base):
    __tablename__ = "cached_injuries"

    id = sa.Column(sa.Integer, primary_key=True)
    team_id = sa.Column(sa.Integer)
    season = sa.Column(sa.Integer)
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String)

    __table_args__ = (
        sa.UniqueConstraint("team_id", "sport", name="_team_id_sport_uc"),
    )


class CachedH2H(Base):
    __tablename__ = "cached_h2h"

    id = sa.Column(sa.Integer, primary_key=True)
    fixture_id = sa.Column(sa.Integer)
    home_id = sa.Column(sa.Integer)
    away_id = sa.Column(sa.Integer)
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String)

    __table_args__ = (
        sa.UniqueConstraint("fixture_id", "sport", name="_fixture_id_sport_uc"),
    )


class CachedStandings(Base):
    __tablename__ = "cached_standings"

    id = sa.Column(sa.Integer, primary_key=True)
    league_id = sa.Column(sa.Integer)
    team_id = sa.Column(sa.Integer)
    season = sa.Column(sa.Integer)
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String)


class CachedTeamStats(Base):
    __tablename__ = "cached_team_stats"

    id = sa.Column(sa.Integer, primary_key=True)
    team_id = sa.Column(sa.Integer)
    league_id = sa.Column(sa.Integer)
    season = sa.Column(sa.Integer)
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String)
    game_id = sa.Column(sa.Integer, nullable=True)


class CachedTeamResults(Base):
    __tablename__ = "cached_team_results"

    id = sa.Column(sa.Integer, primary_key=True)
    team_id = sa.Column(sa.Integer, index=True)
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String)

    __table_args__ = (
        sa.UniqueConstraint("team_id", "sport", name="_team_id_sport_uc"),
    )


class CachedTeams(Base):
    __tablename__ = "cached_teams"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, unique=True)
    data = sa.Column(sa.JSON)
    last_updated = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String)
