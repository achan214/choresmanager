from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c676d62b14b'
down_revision: Union[str, None] = '0fea8acc8058'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("chores", sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("chores", "created_at")
