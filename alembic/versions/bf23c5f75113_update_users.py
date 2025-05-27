"""Update users

Revision ID: bf23c5f75113
Revises: 156fd64e1e65
Create Date: 2025-05-27 14:21:15.099108

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf23c5f75113'
down_revision: Union[str, None] = '156fd64e1e65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # delete users password_hash column
    op.drop_column('users', 'password_hash')


def downgrade() -> None:
    """Downgrade schema."""
    # add users password_hash column
    op.add_column('users', sa.Column('password_hash', sa.String(128), nullable=False))
