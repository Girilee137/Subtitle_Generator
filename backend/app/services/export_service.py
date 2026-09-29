from html import escape

from app.models.subtitle_segment import SubtitleSegment
from app.utils.timefmt import srt_timestamp, vtt_timestamp


def render_srt(segments: list[SubtitleSegment]) -> str:
    blocks = []
    for index, segment in enumerate(sorted(segments, key=lambda item: item.idx), start=1):
        blocks.append(
            f"{index}\n{srt_timestamp(segment.start_time)} --> {srt_timestamp(segment.end_time)}\n{segment.text}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def render_vtt(segments: list[SubtitleSegment]) -> str:
    blocks = ["WEBVTT"]
    for segment in sorted(segments, key=lambda item: item.idx):
        blocks.append(f"{vtt_timestamp(segment.start_time)} --> {vtt_timestamp(segment.end_time)}\n{segment.text}")
    return "\n\n".join(blocks) + "\n"


def render_txt(segments: list[SubtitleSegment]) -> str:
    return "\n".join(segment.text for segment in sorted(segments, key=lambda item: item.idx)) + "\n"


def render_html(segments: list[SubtitleSegment]) -> str:
    rows = []
    for index, segment in enumerate(sorted(segments, key=lambda item: item.idx), start=1):
        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td>{escape(srt_timestamp(segment.start_time))}</td>"
            f"<td>{escape(srt_timestamp(segment.end_time))}</td>"
            f"<td>{escape(segment.text)}</td>"
            "</tr>"
        )
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>Subtitle export</title>"
        "<style>body{font:16px system-ui,sans-serif;margin:2rem;color:#17202a}"
        "table{border-collapse:collapse;width:100%;max-width:960px}"
        "th,td{border:1px solid #c9d2d9;padding:.6rem;text-align:left;vertical-align:top}"
        "th{background:#eef2f4}td:nth-child(1){width:3rem}td:nth-child(2),td:nth-child(3){white-space:nowrap}</style>"
        "</head><body><h1>Subtitle export</h1><table><thead><tr>"
        "<th>#</th><th>Start</th><th>End</th><th>Text</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table></body></html>"
    )


def render_export(segments: list[SubtitleSegment], fmt: str) -> tuple[str, str]:
    if fmt == "srt":
        return render_srt(segments), "application/x-subrip"
    if fmt == "vtt":
        return render_vtt(segments), "text/vtt"
    if fmt == "txt":
        return render_txt(segments), "text/plain"
    if fmt == "html":
        return render_html(segments), "text/html"
    raise ValueError("Unsupported export format")
