"""add trial_used col to users table

Revision ID: 49e014fe9b92
Revises: 618c67d65c48
Create Date: 2025-06-01 21:37:22.819362

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "49e014fe9b92"
down_revision: Union[str, None] = "618c67d65c48"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
