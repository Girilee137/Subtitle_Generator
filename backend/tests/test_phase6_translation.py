from types import SimpleNamespace

import pytest

from app.ml import gemini
from app.ml.tanglish import fake_tanglish
from app.services.translation_service import opposite_language


@pytest.mark.asyncio
async def test_fake_gemini_translate(monkeypatch) -> None:
    monkeypatch.setattr(
        gemini,
        "get_settings",
        lambda: SimpleNamespace(fake_gemini=True, gemini_rpm=10),
    )
    assert await gemini.translate_texts(["Hello"], "en", "ta") == ["[ta] Hello"]


@pytest.mark.asyncio
async def test_fake_gemini_tanglish(monkeypatch) -> None:
    monkeypatch.setattr(
        gemini,
        "get_settings",
        lambda: SimpleNamespace(fake_gemini=True, gemini_rpm=10),
    )
    output = await gemini.transliterate_tanglish_texts(["\u0bb5\u0ba3\u0b95\u0bcd\u0b95\u0bae\u0bcd"])
    assert output[0].isascii()
    assert "va" in output[0]


def test_fake_tanglish_preserves_english_words() -> None:
    assert "hello" in fake_tanglish("\u0bb5\u0ba3\u0b95\u0bcd\u0b95\u0bae\u0bcd hello")


def test_translation_direction_rules() -> None:
    assert opposite_language("en") == "ta"
    assert opposite_language("ta") == "en"
    with pytest.raises(Exception):
        opposite_language("ta-Latn")
