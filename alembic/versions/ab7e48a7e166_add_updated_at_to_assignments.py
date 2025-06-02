"""Add updated_at to assignments

Revision ID: ab7e48a7e166
Revises: 46a0b502e781
Create Date: 2025-06-01 18:37:34.648051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab7e48a7e166'
down_revision: Union[str, None] = '46a0b502e781'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('assignments', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('assignments', 'updated_at')
