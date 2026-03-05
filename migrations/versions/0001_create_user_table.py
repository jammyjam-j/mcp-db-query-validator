"""Revision ID: 0001_create_user_table
Revises: 
Create Date: 2026-03-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow, nullable=False)
    )


def downgrade() -> None:
    op.drop_table('users')