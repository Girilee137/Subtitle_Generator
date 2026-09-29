"""add html export format

Revision ID: 0002_add_html_export_format
Revises: 0001_initial_schema
Create Date: 2026-09-25
"""
from alembic import op

revision = "0002_add_html_export_format"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE export_format ADD VALUE IF NOT EXISTS 'html'")


def downgrade() -> None:
    # PostgreSQL does not support removing an enum value in place.
    pass
