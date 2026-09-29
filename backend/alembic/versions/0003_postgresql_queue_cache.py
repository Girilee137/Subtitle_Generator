"""replace Redis coordination with PostgreSQL queue and cache

Revision ID: 0003_postgresql_queue_cache
Revises: 0002_add_html_export_format
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_postgresql_queue_cache"
down_revision = "0002_add_html_export_format"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("jobs", "celery_root_id")
    op.create_table(
        "cache_entries",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "queued_tasks",
        sa.Column("task_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_name", sa.String(length=80), nullable=False),
        sa.Column("queue_name", sa.String(length=20), nullable=False, server_default="default"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="QUEUED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.Text()),
    )
    op.create_index(
        "ix_queued_tasks_claim",
        "queued_tasks",
        ["queue_name", "status", "priority", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_queued_tasks_claim", table_name="queued_tasks")
    op.drop_table("queued_tasks")
    op.drop_table("cache_entries")
    op.add_column("jobs", sa.Column("celery_root_id", sa.Text()))
