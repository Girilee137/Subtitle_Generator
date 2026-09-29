from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import TrackKind


class SegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    segment_id: UUID
    track_id: UUID
    idx: int
    start_time: float
    end_time: float
    text: str
    confidence: float
    created_at: datetime
    updated_at: datetime


class TrackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    track_id: UUID
    file_id: UUID
    language: str
    source_language: str | None
    is_translated: bool
    kind: TrackKind
    created_at: datetime
    updated_at: datetime


class TrackWithSegments(TrackRead):
    segments: list[SegmentRead]


class SegmentUpdate(BaseModel):
    text: str | None = Field(default=None, max_length=5000)
    start_time: float | None = Field(default=None, ge=0)
    end_time: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_payload(self):
        if self.text is None and self.start_time is None and self.end_time is None:
            raise ValueError("At least one field is required")
        if self.start_time is not None and self.end_time is not None and self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        return self


class SegmentSplitRequest(BaseModel):
    at_time: float = Field(gt=0)
    at_char: int = Field(ge=1)


class TrackShiftRequest(BaseModel):
    offset: float
    from_idx: int | None = Field(default=None, ge=0)


class TrackMergeRequest(BaseModel):
    segment_a: UUID
    segment_b: UUID
