"""Update groups table

Revision ID: 156fd64e1e65
Revises: ad005fcf4f64
Create Date: 2025-05-27 14:04:41.304747

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '156fd64e1e65'
down_revision: Union[str, None] = 'ad005fcf4f64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # name is now group_name
    op.alter_column('groups', 'name', new_column_name='group_name')
    # Add unique constraint to 'username'
    op.create_unique_constraint('uq_grp_groupname', 'groups', ['group_name'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove unique constraint from 'group_name'
    op.drop_constraint('uq_grp_groupname', 'groups', type_='unique')
    # Rename 'group_name' column back to 'name'
    op.alter_column('groups', 'group_name', new_column_name='name')
