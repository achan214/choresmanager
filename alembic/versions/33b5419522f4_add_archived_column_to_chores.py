"""Add archived column to chores

Revision ID: 33b5419522f4
Revises: ab7e48a7e166
Create Date: 2025-06-01 18:41:10.722421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33b5419522f4'
down_revision: Union[str, None] = 'ab7e48a7e166'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chores", sa.Column("archived", sa.Boolean(), nullable=False, server_default="false"))

def downgrade() -> None:
    op.drop_column("chores", "archived")

