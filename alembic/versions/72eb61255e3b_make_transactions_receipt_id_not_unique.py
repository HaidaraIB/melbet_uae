"""make transactions.receipt_id not unique

Revision ID: 72eb61255e3b
Revises: e5d65c093ad0
Create Date: 2025-07-02 20:50:12.782543

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "72eb61255e3b"
down_revision: Union[str, None] = "e5d65c093ad0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column(
            "receipt_id",
            existing_type=sa.String(),
            nullable=True,
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column(
            "receipt_id",
            existing_type=sa.String(),
            nullable=True,
            unique=True,
        )
