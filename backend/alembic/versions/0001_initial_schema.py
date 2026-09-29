"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    role = postgresql.ENUM("USER", "ADMIN", name="role", create_type=False)
    processing_status = postgresql.ENUM(
        "QUEUED", "PROCESSING", "COMPLETED", "FAILED", "PAUSED", name="processing_status", create_type=False
    )
    job_mode = postgresql.ENUM("SERVER", "BROWSER", name="job_mode", create_type=False)
    job_stage = postgresql.ENUM(
        "extract", "detect_lang", "vad", "chunk", "schedule", "asr", "align", "segment", "tanglish", "done",
        name="job_stage",
        create_type=False,
    )
    track_kind = postgresql.ENUM("ORIGINAL", "TRANSLATION", "TRANSLITERATION", name="track_kind", create_type=False)
    export_format = postgresql.ENUM("srt", "vtt", "txt", name="export_format", create_type=False)
    bind = op.get_bind()
    role.create(bind, checkfirst=True)
    processing_status.create(bind, checkfirst=True)
    job_mode.create(bind, checkfirst=True)
    job_stage.create(bind, checkfirst=True)
    track_kind.create(bind, checkfirst=True)
    export_format.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("storage_used", sa.BigInteger(), nullable=False),
        sa.Column("server_processing_consent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.execute("CREATE UNIQUE INDEX ix_users_email_lower ON users (lower(email))")

    op.create_table(
        "admin_profiles",
        sa.Column("admin_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permissions", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("admin_id"),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("token_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_id"),
    )
    op.create_table(
        "projects",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("status", processing_status, nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id"),
    )
    op.create_index("ix_projects_owner_status", "projects", ["owner_id", "status"])
    op.create_index("ix_projects_search_vector", "projects", ["search_vector"], postgresql_using="gin")
    op.execute(
        "CREATE TRIGGER projects_search_vector_update BEFORE INSERT OR UPDATE OF title ON projects "
        "FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(search_vector, 'pg_catalog.english', title)"
    )

    op.create_table(
        "media_files",
        sa.Column("file_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("is_stored", sa.Boolean(), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=True),
        sa.Column("audio_path", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("file_id"),
    )
    op.create_table(
        "subtitle_tracks",
        sa.Column("track_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("source_language", sa.String(length=16), nullable=True),
        sa.Column("is_translated", sa.Boolean(), nullable=False),
        sa.Column("kind", track_kind, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["media_files.file_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("track_id"),
    )
    op.create_index("ix_subtitle_tracks_file_kind", "subtitle_tracks", ["file_id", "kind"])
    op.create_table(
        "subtitle_segments",
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("end_time > start_time", name="segment_end_after_start"),
        sa.ForeignKeyConstraint(["track_id"], ["subtitle_tracks.track_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("segment_id"),
        sa.UniqueConstraint("track_id", "idx", name="uq_subtitle_segments_track_idx"),
    )
    op.create_index("ix_subtitle_segments_track_idx", "subtitle_segments", ["track_id", "idx"])
    op.create_index("ix_subtitle_segments_search_vector", "subtitle_segments", ["search_vector"], postgresql_using="gin")
    op.execute(
        "CREATE TRIGGER subtitle_segments_search_vector_update BEFORE INSERT OR UPDATE OF text ON subtitle_segments "
        "FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(search_vector, 'pg_catalog.simple', text)"
    )
    op.create_table(
        "jobs",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mode", job_mode, nullable=False),
        sa.Column("status", processing_status, nullable=False),
        sa.Column("stage", job_stage, nullable=True),
        sa.Column("progress", sa.Float(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("chunks_total", sa.Integer(), nullable=False),
        sa.Column("chunks_done", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("celery_root_id", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["media_files.file_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index("ix_jobs_project_status", "jobs", ["project_id", "status"])
    op.create_table(
        "job_chunks",
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("start_s", sa.Float(), nullable=False),
        sa.Column("end_s", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("end_s > start_s", name="chunk_end_after_start"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chunk_id"),
    )
    op.create_index("ix_job_chunks_job_idx", "job_chunks", ["job_id", "idx"], unique=True)
    op.create_table(
        "system_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("detail", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.user_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "export_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("format", export_format, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["track_id"], ["subtitle_tracks.track_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("export_records")
    op.drop_table("system_logs")
    op.drop_index("ix_job_chunks_job_idx", table_name="job_chunks")
    op.drop_table("job_chunks")
    op.drop_index("ix_jobs_project_status", table_name="jobs")
    op.drop_table("jobs")
    op.execute("DROP TRIGGER IF EXISTS subtitle_segments_search_vector_update ON subtitle_segments")
    op.drop_index("ix_subtitle_segments_search_vector", table_name="subtitle_segments")
    op.drop_index("ix_subtitle_segments_track_idx", table_name="subtitle_segments")
    op.drop_table("subtitle_segments")
    op.drop_index("ix_subtitle_tracks_file_kind", table_name="subtitle_tracks")
    op.drop_table("subtitle_tracks")
    op.drop_table("media_files")
    op.execute("DROP TRIGGER IF EXISTS projects_search_vector_update ON projects")
    op.drop_index("ix_projects_search_vector", table_name="projects")
    op.drop_index("ix_projects_owner_status", table_name="projects")
    op.drop_table("projects")
    op.drop_table("refresh_tokens")
    op.drop_table("admin_profiles")
    op.drop_index("ix_users_email_lower", table_name="users")
    op.drop_table("users")
    for enum_name in ("export_format", "track_kind", "job_stage", "job_mode", "processing_status", "role"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
