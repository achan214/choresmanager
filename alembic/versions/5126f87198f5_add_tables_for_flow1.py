"""Add tables for flow1

Revision ID: 5126f87198f5
Revises: e91d0c24f7d0
Create Date: 2025-05-11 00:16:39.195993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5126f87198f5'
down_revision: Union[str, None] = 'e91d0c24f7d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("global_inventory")

    # create table for groups
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("invite_code", sa.String(10), nullable=False),
    )

    # create table for users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("email", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(128), nullable=False),
        sa.Column("is_admin", sa.Boolean, default=False),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("groups.id"), nullable=True),
    )

    #create table for chores
    op.create_table(
        "chores",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.String(200), nullable=False),
        sa.Column("due_date", sa.DateTime, nullable=False),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("is_recurring", sa.Boolean, default=False),
        sa.Column("recurrence_pattern", sa.String(50), nullable=True),
        sa.Column("completed", sa.Boolean, default=False),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    # create table for chore assignments
    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("chore_id", sa.Integer, sa.ForeignKey("chores.id"), nullable=False),
        sa.Column("assigned_at", sa.DateTime, nullable=False),
        sa.Column("completed_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
    )



def downgrade() -> None:
    
    op.drop_table("assignments")
    op.drop_table("chores")
    op.drop_table("users")
    op.drop_table("groups")

    # recreate global inventory
    op.create_table(
        "global_inventory",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("gold", sa.Integer, nullable=False),
        sa.CheckConstraint("gold >= 0", name="check_gold_positive"),
    )

    op.execute(sa.text("INSERT INTO global_inventory (gold) VALUES (100)"))
