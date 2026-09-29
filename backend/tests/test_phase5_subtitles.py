from types import SimpleNamespace

import pytest

from app.core.errors import BadRequestError
from app.services.subtitle_service import normalize_indexes, validate_no_overlap, validate_timing


def segment(idx: int, start: float, end: float):
    return SimpleNamespace(idx=idx, start_time=start, end_time=end)


def test_validate_timing_requires_end_after_start() -> None:
    validate_timing(0.0, 1.0)
    with pytest.raises(BadRequestError):
        validate_timing(1.0, 1.0)


def test_validate_no_overlap_accepts_touching_segments() -> None:
    validate_no_overlap([segment(0, 0.0, 1.0), segment(1, 1.0, 2.0)])


def test_validate_no_overlap_rejects_overlap() -> None:
    with pytest.raises(BadRequestError):
        validate_no_overlap([segment(0, 0.0, 1.1), segment(1, 1.0, 2.0)])


def test_normalize_indexes_orders_by_timing() -> None:
    late = segment(9, 5.0, 6.0)
    early = segment(3, 1.0, 2.0)
    normalize_indexes([late, early])
    assert early.idx == 0
    assert late.idx == 1
