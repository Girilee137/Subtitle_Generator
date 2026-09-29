from pydantic import BaseModel, Field, field_validator

from app.core.config import SUPPORTED_LANGUAGES


class MetadataFileCreate(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    file_type: str = Field(min_length=1, max_length=120)
    size_bytes: int = Field(ge=0)
    duration_seconds: float | None = Field(default=None, ge=0)


class ClientWord(BaseModel):
    word: str = Field(min_length=1, max_length=64)
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    prob: float | None = Field(default=None, ge=0, le=1)

    @field_validator("word")
    @classmethod
    def strip_control_chars(cls, value: str) -> str:
        return "".join(char for char in value.strip() if char.isprintable())


class ClientResultRequest(BaseModel):
    language: str
    model: str = Field(min_length=1, max_length=200)
    words: list[ClientWord]

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        if value not in SUPPORTED_LANGUAGES:
            raise ValueError("language must be en or ta")
        return value


class UserQuotaRead(BaseModel):
    server_jobs_used: int
    server_jobs_limit: int
    storage_used: int
    storage_quota: int
