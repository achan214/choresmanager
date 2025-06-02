"""Add completed_by to assignments

Revision ID: 46a0b502e781
Revises: 0c676d62b14b
Create Date: 2025-06-01 18:28:18.199879

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46a0b502e781'
down_revision: Union[str, None] = '0c676d62b14b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("assignments", sa.Column("completed_by", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_assignments_completed_by_users", "assignments", "users", ["completed_by"], ["id"]
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_assignments_completed_by_users", "assignments", type_="foreignkey")
    op.drop_column("assignments", "completed_by")

