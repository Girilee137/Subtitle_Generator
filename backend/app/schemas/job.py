from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import JobMode, JobStage, ProcessingStatus


class ProcessRequest(BaseModel):
    language: str = Field(default="auto")
    priority: int = Field(default=5, ge=0, le=9)


class ProcessAccepted(BaseModel):
    job_id: UUID


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: UUID
    project_id: UUID
    file_id: UUID
    mode: JobMode
    status: ProcessingStatus
    stage: JobStage | None
    progress: float
    priority: int
    chunks_total: int
    chunks_done: int
    error: str | None
    created_at: datetime
    updated_at: datetime
