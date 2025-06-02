"""Add completed_by column to chores

Revision ID: 0fea8acc8058
Revises: bf23c5f75113
Create Date: 2025-06-01 15:44:36.480173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fea8acc8058'
down_revision: Union[str, None] = 'bf23c5f75113'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("chores", sa.Column("completed_by", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_completed_by_users", "chores", "users", ["completed_by"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_completed_by_users", "chores", type_="foreignkey")
    op.drop_column("chores", "completed_by")

