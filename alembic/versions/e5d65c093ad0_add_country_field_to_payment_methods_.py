"""add country field to payment_methods table

Revision ID: e5d65c093ad0
Revises: 49e014fe9b92
Create Date: 2025-06-21 03:59:39.420761

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5d65c093ad0"
down_revision: Union[str, None] = "49e014fe9b92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("payment_methods") as batch_op:
        batch_op.add_column(
            sa.Column(
                name="country",
                type_=sa.String,
                server_default="uae",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("payment_methods") as batch_op:
        batch_op.drop_column("country")
