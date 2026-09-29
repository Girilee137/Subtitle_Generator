from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

SUPPORTED_LANGUAGES = ["en", "ta"]
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
        enable_decoding=False,
    )

    database_url: str = "postgresql+asyncpg://subtitle:subtitle@localhost:5432/subtitle_platform"
    sync_database_url: str | None = None
    storage_backend: str = "local"
    r2_endpoint_url: str = ""
    r2_bucket: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_region: str = "auto"
    jwt_secret: str = "dev-secret-change-me"
    storage_root: Path = Path("storage")
    max_upload_mb: int = 500
    user_quota_mb: int = 5000
    whisper_model: str = "medium"
    whisper_device: str = "auto"
    asr_provider: str = "whisper"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    gemini_rpm: int = 10
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@example.local"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    fake_asr: bool = False
    fake_gemini: bool = False
    server_jobs_per_day: int = 5
    client_result_max_words: int = 200000
    admin_email: str = "admin@example.local"
    admin_password: str = "change-me-admin"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    password_reset_minutes: int = 30

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_async_database_url(cls, value: str) -> str:
        url = make_url(value)
        if url.drivername in {"postgres", "postgresql"}:
            url = url.set(drivername="postgresql+asyncpg")
        query = dict(url.query)
        if query.get("sslmode") in {"require", "verify-ca", "verify-full"}:
            query["ssl"] = query.pop("sslmode")
        query.pop("channel_binding", None)
        return url.set(query=query).render_as_string(hide_password=False)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("storage_backend")
    @classmethod
    def validate_storage_backend(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"local", "r2"}:
            raise ValueError("STORAGE_BACKEND must be either 'local' or 'r2'")
        return normalized

    @property
    def sync_db_url(self) -> str:
        url = make_url(self.sync_database_url or self.database_url)
        if url.drivername in {"postgres", "postgresql", "postgresql+asyncpg"}:
            url = url.set(drivername="postgresql+psycopg")
        query = dict(url.query)
        if query.get("ssl") in {"require", "verify-ca", "verify-full"}:
            query["sslmode"] = query.pop("ssl")
        return url.set(query=query).render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
