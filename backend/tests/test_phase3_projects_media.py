import uuid
from types import SimpleNamespace

import pytest

from app.core.errors import BadRequestError, ConflictError
from app.api.v1.files import parse_range
from app.models.enums import ProcessingStatus
from app.services import search_service
from app.services.media_service import storage_dir
from app.services.state_machine import transition
from app.utils.trie import Trie


def test_state_machine_legal_transitions() -> None:
    project = SimpleNamespace(status=None, deleted_at=None)
    transition(project, "createProject")
    assert project.status == ProcessingStatus.QUEUED
    transition(project, "startProcessing")
    assert project.status == ProcessingStatus.PROCESSING
    transition(project, "processingCompleted")
    assert project.status == ProcessingStatus.COMPLETED
    transition(project, "pauseProcessing")
    assert project.status == ProcessingStatus.PAUSED
    transition(project, "resumeProcessing")
    assert project.status == ProcessingStatus.COMPLETED


def test_state_machine_rejects_illegal_transition() -> None:
    project = SimpleNamespace(status=ProcessingStatus.FAILED, deleted_at=None)
    with pytest.raises(ConflictError):
        transition(project, "pauseProcessing")


def test_state_machine_soft_delete_sets_timestamp() -> None:
    project = SimpleNamespace(status=ProcessingStatus.QUEUED, deleted_at=None)
    transition(project, "deleteProject")
    assert project.deleted_at is not None


def test_trie_insert_delete_prefix() -> None:
    trie = Trie()
    trie.insert("Tamil Demo")
    trie.insert("English Demo")
    assert trie.prefix_search("ta") == ["Tamil Demo"]
    trie.delete("Tamil Demo")
    assert trie.prefix_search("ta") == []


def test_project_suggestion_hooks() -> None:
    user_id = uuid.uuid4()
    search_service.project_created(user_id, "First Project")
    assert search_service.suggest_projects(user_id, "fir") == ["First Project"]
    search_service.project_renamed(user_id, "First Project", "Renamed Project")
    assert search_service.suggest_projects(user_id, "fir") == []
    assert search_service.suggest_projects(user_id, "ren") == ["Renamed Project"]
    search_service.project_deleted(user_id, "Renamed Project")
    assert search_service.suggest_projects(user_id, "ren") == []


def test_parse_range() -> None:
    assert parse_range("bytes=10-19", 100) == (10, 19)
    assert parse_range("bytes=10-", 100) == (10, 99)
    assert parse_range("bytes=-20", 100) == (80, 99)
    with pytest.raises(BadRequestError):
        parse_range("items=10-19", 100)


def test_storage_layout_contains_user_project_file_ids() -> None:
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    file_id = uuid.uuid4()
    path = storage_dir(user_id, project_id, file_id)
    assert str(user_id) in str(path)
    assert str(project_id) in str(path)
    assert str(file_id) in str(path)
