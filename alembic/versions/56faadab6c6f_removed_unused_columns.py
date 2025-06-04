"""removed unused columns

Revision ID: 56faadab6c6f
Revises: 33b5419522f4
Create Date: 2025-06-04 01:01:39.223746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56faadab6c6f'
down_revision: Union[str, None] = '33b5419522f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # remove updated_at for assignments
    op.drop_column('assignments', 'updated_at')

    # removed completed_at and completed_by for chores
    op.drop_column('chores', 'completed_at')
    op.drop_column('chores', 'completed_by')


def downgrade() -> None:
    """Downgrade schema."""
    # add updated_at for assignments
    op.add_column('assignments', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # add completed_at and completed_by for chores
    op.add_column('chores', sa.Column('completed_at', sa.DateTime(), nullable=True))
    op.add_column('chores', sa.Column('completed_by', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_chores_completed_by_users', 'chores', 'users', ['completed_by'], ['id']
    ) 
