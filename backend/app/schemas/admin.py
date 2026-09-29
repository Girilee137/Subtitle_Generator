from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import JobMode, JobStage, ProcessingStatus, Role


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    name: str
    email: str
    role: Role
    is_active: bool
    storage_used: int
    created_at: datetime


class AdminJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: UUID
    project_id: UUID
    file_id: UUID
    mode: JobMode
    status: ProcessingStatus
    stage: JobStage | None
    progress: float
    chunks_done: int
    chunks_total: int
    error: str | None
    created_at: datetime


class AdminLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ts: datetime
    level: str
    actor_id: UUID | None
    action: str
    detail: dict


class StorageSummary(BaseModel):
    storage_used: int
    files_count: int
    stored_files_count: int


class AnalyticsRead(BaseModel):
    users: int
    active_users: int
    projects_by_status: dict[str, int]
    storage_used: int
    jobs_by_mode: dict[str, int]
    jobs_by_day: dict[str, int]
    avg_processing_seconds: float | None
