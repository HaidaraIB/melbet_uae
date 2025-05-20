"""delete recommendation_history table and scheduled_fixtures table

Revision ID: b11bc60ee3d9
Revises: 
Create Date: 2025-05-20 01:26:17.329424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b11bc60ee3d9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("recommendation_history")
    op.drop_table("scheduled_fixtures")


def downgrade() -> None:
    pass
