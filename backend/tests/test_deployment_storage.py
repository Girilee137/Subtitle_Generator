from pathlib import Path

import pytest

from app.core.config import Settings
from app.services import object_storage


def test_neon_postgres_url_supports_async_and_sync_sqlalchemy_drivers() -> None:
    settings = Settings(
        database_url="postgresql://dbuser:secret@neon.example/db?sslmode=require&channel_binding=require",
        _env_file=None,
    )

    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert "ssl=require" in settings.database_url
    assert "channel_binding" not in settings.database_url
    assert settings.sync_db_url.startswith("postgresql+psycopg://")
    assert "sslmode=require" in settings.sync_db_url


def test_explicit_sync_database_url_uses_psycopg_driver() -> None:
    settings = Settings(
        database_url="postgresql://owner@neon.example/db?sslmode=require",
        sync_database_url="postgresql://owner@neon.example/db?sslmode=require",
        _env_file=None,
    )

    assert settings.sync_db_url.startswith("postgresql+psycopg://")
    assert "sslmode=require" in settings.sync_db_url


def test_default_gemini_model_is_flash() -> None:
    settings = Settings(_env_file=None)

    assert settings.gemini_model == "gemini-3.8-flash"


@pytest.mark.asyncio
async def test_local_object_storage_adapter_round_trip(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(object_storage, "uses_r2", lambda: False)
    local_object = tmp_path / "owner" / "project" / "media" / "original.wav"
    source = tmp_path / "upload.wav"
    downloaded = tmp_path / "worker" / "original.wav"
    source.write_bytes(b"test audio")

    await object_storage.upload_file(source, str(local_object))
    assert await object_storage.get_file_size(str(local_object)) == len(b"test audio")
    await object_storage.download_file(str(local_object), downloaded)
    assert downloaded.read_bytes() == b"test audio"
    assert b"".join(object_storage.iter_file_range(str(local_object), 2, 5)) == b"st a"
    await object_storage.delete_file(str(local_object))
    assert not local_object.exists()
