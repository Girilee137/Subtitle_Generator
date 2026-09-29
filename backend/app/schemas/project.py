from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ProcessingStatus


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: UUID
    owner_id: UUID
    title: str
    status: ProcessingStatus
    created_at: datetime
    updated_at: datetime


class ProjectList(BaseModel):
    items: list[ProjectRead]
    total: int


class MediaFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_id: UUID
    project_id: UUID
    file_name: str
    file_type: str
    size_bytes: int
    duration_seconds: float | None
    is_stored: bool
    created_at: datetime
