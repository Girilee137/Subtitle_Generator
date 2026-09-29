from types import SimpleNamespace

import pytest

from app.ml.aligner import cleanup_words
from app.ml.chunker import chunk_intervals
from app.ml.fake_asr import transcribe_fake
from app.ml.segmenter import grapheme_len, segment_words
from app.models.enums import ProcessingStatus
from app.services.state_machine import transition
from app.models.queued_task import QueuedTask
from app.services import processing_service


def test_fake_asr_has_english_and_tamil_samples() -> None:
    english = transcribe_fake("en")
    tamil = transcribe_fake("ta")
    assert english[0]["word"] == "Hello"
    assert tamil[0]["word"] == "வணக்கம்"


def test_chunker_splits_long_intervals_to_thirty_seconds() -> None:
    chunks = chunk_intervals([(0.0, 75.0)])
    assert chunks == [(0.0, 30.0), (30.0, 60.0), (60.0, 75.3)]


def test_aligner_offsets_and_clamps_overlaps() -> None:
    words = cleanup_words(
        [
            {"word": "A", "start": 0.0, "end": 1.0, "prob": 0.8},
            {"word": "B", "start": 0.5, "end": 1.5, "prob": 0.9},
        ],
        offset=10.0,
    )
    assert words[0]["start"] == 10.0
    assert words[1]["start"] >= words[0]["end"]


def test_segmenter_prefers_punctuation_and_counts_tamil_graphemes() -> None:
    words = [
        {"word": "Hello.", "start": 0.0, "end": 0.5, "prob": 0.9},
        {"word": "This", "start": 1.0, "end": 1.3, "prob": 0.9},
        {"word": "is", "start": 1.4, "end": 1.6, "prob": 0.9},
        {"word": "test.", "start": 1.7, "end": 2.0, "prob": 0.9},
    ]
    segments = segment_words(words, "en")
    assert segments[0].text.endswith(".")
    assert grapheme_len("கி") == 1


def test_state_machine_processing_pause_resume_extension() -> None:
    project = SimpleNamespace(status=ProcessingStatus.PROCESSING, deleted_at=None)
    transition(project, "pauseProcessing")
    assert project.status == ProcessingStatus.PAUSED
    transition(project, "resumeProcessing", unfinished_job=True)
    assert project.status == ProcessingStatus.PROCESSING


def test_postgres_queue_prioritizes_lower_values() -> None:
    earlier = QueuedTask(task_name="process_job", payload={}, priority=1, queue_name="gpu")
    later = QueuedTask(task_name="process_job", payload={}, priority=5, queue_name="gpu")
    assert earlier.priority < later.priority


@pytest.mark.asyncio
async def test_completed_server_job_deletes_media_and_releases_storage(monkeypatch) -> None:
    owner_id = "owner"
    owner = SimpleNamespace(storage_used=100)
    media = SimpleNamespace(
        file_id="file",
        size_bytes=40,
        is_stored=True,
        storage_path="users/owner/file.wav",
        audio_path="users/owner/audio.wav",
    )
    job = SimpleNamespace(
        job_id="job",
        status=ProcessingStatus.COMPLETED,
        mode=processing_service.JobMode.SERVER,
        media_file=media,
        project=SimpleNamespace(owner_id=owner_id),
    )
    deleted_paths: list[str] = []

    async def delete_file(path: str) -> None:
        assert job.status == ProcessingStatus.COMPLETED
        deleted_paths.append(path)

    async def write_log(*args, **kwargs) -> None:
        pass

    class FakeSession:
        async def get(self, model, key):
            return owner

        async def commit(self) -> None:
            pass

        async def rollback(self) -> None:
            pass

    monkeypatch.setattr("app.services.object_storage.delete_file", delete_file)
    monkeypatch.setattr(processing_service, "write_system_log", write_log)

    await processing_service.cleanup_completed_server_media(FakeSession(), job)

    assert deleted_paths == ["users/owner/file.wav"]
    assert media.is_stored is False
    assert media.storage_path is None
    assert media.audio_path is None
    assert owner.storage_used == 60


@pytest.mark.asyncio
async def test_media_cleanup_failure_keeps_metadata_and_quota(monkeypatch) -> None:
    owner_id = "owner"
    owner = SimpleNamespace(storage_used=100)
    media = SimpleNamespace(
        file_id="file",
        size_bytes=40,
        is_stored=True,
        storage_path="users/owner/file.wav",
        audio_path="users/owner/audio.wav",
    )
    job = SimpleNamespace(
        job_id="job",
        status=ProcessingStatus.COMPLETED,
        mode=processing_service.JobMode.SERVER,
        media_file=media,
        project=SimpleNamespace(owner_id=owner_id),
    )
    logs: list[dict] = []

    async def delete_file(path: str) -> None:
        raise OSError("storage unavailable")

    async def write_log(session, action: str, detail: dict, **kwargs) -> None:
        logs.append({"action": action, "detail": detail, **kwargs})

    class FakeSession:
        async def get(self, model, key):
            return owner

        async def commit(self) -> None:
            pass

        async def rollback(self) -> None:
            pass

    monkeypatch.setattr("app.services.object_storage.delete_file", delete_file)
    monkeypatch.setattr(processing_service, "write_system_log", write_log)

    await processing_service.cleanup_completed_server_media(FakeSession(), job)

    assert media.is_stored is True
    assert media.storage_path == "users/owner/file.wav"
    assert media.audio_path == "users/owner/audio.wav"
    assert owner.storage_used == 100
    assert logs[0]["action"] == "media.auto_delete_after_transcription.failed"
