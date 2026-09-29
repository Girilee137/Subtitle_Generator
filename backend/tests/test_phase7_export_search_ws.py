from types import SimpleNamespace

from app.services.export_service import render_export, render_html, render_srt, render_txt, render_vtt
from app.utils.timefmt import srt_timestamp, vtt_timestamp
from app.utils.trie import Trie


def seg(idx: int, start: float, end: float, text: str):
    return SimpleNamespace(idx=idx, start_time=start, end_time=end, text=text)


def test_subtitle_timestamps() -> None:
    assert srt_timestamp(3661.234) == "01:01:01,234"
    assert vtt_timestamp(1.5) == "00:00:01.500"


def test_srt_export() -> None:
    body = render_srt([seg(0, 0.0, 1.25, "Hello")])
    assert "1\n00:00:00,000 --> 00:00:01,250\nHello" in body


def test_vtt_export() -> None:
    body = render_vtt([seg(0, 0.0, 1.0, "Hello")])
    assert body.startswith("WEBVTT")
    assert "00:00:00.000 --> 00:00:01.000" in body


def test_txt_export() -> None:
    assert render_txt([seg(1, 1.0, 2.0, "B"), seg(0, 0.0, 1.0, "A")]) == "A\nB\n"


def test_html_export_escapes_subtitle_text() -> None:
    body = render_html([seg(0, 0.0, 1.0, "<Hello> & welcome")])
    assert "<title>Subtitle export</title>" in body
    assert "&lt;Hello&gt; &amp; welcome" in body


def test_render_export_dispatch() -> None:
    assert render_export([seg(0, 0.0, 1.0, "A")], "txt")[1] == "text/plain"


def test_trie_suggest_delete() -> None:
    trie = Trie()
    trie.insert("Alpha")
    trie.insert("Alpine")
    assert trie.prefix_search("alp") == ["Alpha", "Alpine"]
    trie.delete("Alpha")
    assert trie.prefix_search("alp") == ["Alpine"]
