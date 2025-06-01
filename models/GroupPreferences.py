from models.DB import Base
import sqlalchemy as sa


class GroupPreferences(Base):
    __tablename__ = "group_preferences"
    id = sa.Column(sa.Integer, primary_key=True)
    group_id = sa.Column(sa.BigInteger, unique=True, index=True)
    language = sa.Column(sa.String, default="ar")  # ar, en, fr, ...
    dialect = sa.Column(sa.String, default="msa")  # msa (فصحى), egy, sy, sa, ...
    sports = sa.Column(
        sa.JSON, default=dict
    )  # {"football": [league_id1, ...], "basketball": [...]} (فارغة = كل الرياضات/الدوريات)
    brands = sa.Column(sa.JSON, default=list)  # <-- الآن قائمة
