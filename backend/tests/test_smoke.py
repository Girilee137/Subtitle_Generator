from fastapi.testclient import TestClient

from app.core.config import SUPPORTED_LANGUAGES, get_settings
from app.db.base import Base
from app.main import app
import app.models as _models  # noqa: F401


def test_supported_languages_fixed() -> None:
    assert SUPPORTED_LANGUAGES == ["en", "ta"]


def test_metadata_contains_phase_one_tables() -> None:
    expected = {
        "users",
        "admin_profiles",
        "refresh_tokens",
        "projects",
        "media_files",
        "subtitle_tracks",
        "subtitle_segments",
        "jobs",
        "job_chunks",
        "system_logs",
        "export_records",
    }
    assert expected.issubset(Base.metadata.tables.keys())


def test_health_endpoint_shape() -> None:
    get_settings.cache_clear()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"status", "db", "postgres_queue", "storage", "gpu"}
