"""Update users table

Revision ID: ad005fcf4f64
Revises: 5126f87198f5
Create Date: 2025-05-27 14:00:22.144630

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad005fcf4f64'
down_revision: Union[str, None] = '5126f87198f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # edit users table to make name column called "username" and must be unique
    op.alter_column('users', 'name', new_column_name='username')
    # Add unique constraint to 'username'
    op.create_unique_constraint('uq_users_username', 'users', ['username'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove unique constraint from 'username'
    op.drop_constraint('uq_users_username', 'users', type_='unique')
    # Rename 'username' column back to 'name'
    op.alter_column('users', 'username', new_column_name='name')
