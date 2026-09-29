from pydantic import BaseModel, field_validator

from app.core.config import SUPPORTED_LANGUAGES


class TranslateRequest(BaseModel):
    target_language: str

    @field_validator("target_language")
    @classmethod
    def validate_target(cls, value: str) -> str:
        if value not in SUPPORTED_LANGUAGES:
            raise ValueError("target_language must be en or ta")
        return value
