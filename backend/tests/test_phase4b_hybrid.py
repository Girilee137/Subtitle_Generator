from types import SimpleNamespace

import pytest

from app.core.errors import BadRequestError, PayloadTooLargeError
from app.models.enums import ProcessingStatus
from app.schemas.hybrid import ClientWord
from app.services.client_result_service import validate_client_words
from app.services.state_machine import transition


def word(text: str, start: float, end: float, prob: float | None = None) -> ClientWord:
    return ClientWord(word=text, start=start, end=end, prob=prob)


def test_client_words_default_probability_and_validation() -> None:
    clean = validate_client_words([word("hello", 0.0, 0.5, None)], duration_seconds=1.0)
    assert clean == [{"word": "hello", "start": 0.0, "end": 0.5, "prob": 0.9}]


def test_client_words_reject_non_monotonic_times() -> None:
    with pytest.raises(BadRequestError):
        validate_client_words([word("late", 1.0, 1.5), word("early", 0.5, 0.8)], duration_seconds=2.0)


def test_client_words_reject_end_beyond_duration() -> None:
    with pytest.raises(BadRequestError):
        validate_client_words([word("too-far", 0.0, 3.1)], duration_seconds=2.0)


def test_client_words_reject_oversized_payload(monkeypatch) -> None:
    from app.services import client_result_service

    monkeypatch.setattr(client_result_service, "get_settings", lambda: SimpleNamespace(client_result_max_words=1))
    with pytest.raises(PayloadTooLargeError):
        validate_client_words([word("one", 0.0, 0.2), word("two", 0.3, 0.5)], duration_seconds=1.0)


def test_browser_mode_state_machine_path() -> None:
    project = SimpleNamespace(status=ProcessingStatus.QUEUED, deleted_at=None)
    transition(project, "startProcessing")
    assert project.status == ProcessingStatus.PROCESSING
    transition(project, "processingCompleted")
    assert project.status == ProcessingStatus.COMPLETED


def test_failed_project_can_retry_before_browser_result() -> None:
    project = SimpleNamespace(status=ProcessingStatus.FAILED, deleted_at=None)
    transition(project, "retryProcessing")
    assert project.status == ProcessingStatus.QUEUED
