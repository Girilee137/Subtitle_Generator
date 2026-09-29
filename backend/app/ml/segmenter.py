import math
from dataclasses import dataclass

import regex


@dataclass(frozen=True)
class SubtitleSegmentDraft:
    idx: int
    start_time: float
    end_time: float
    text: str
    confidence: float


LIMITS = {
    "en": {"max_chars": 84, "target": 37},
    "ta": {"max_chars": 64, "target": 28},
}


def grapheme_len(text: str) -> int:
    return len(regex.findall(r"\X", text))


def segment_words(words: list[dict], language: str) -> list[SubtitleSegmentDraft]:
    if not words:
        return []
    limits = LIMITS.get(language, LIMITS["en"])
    n = len(words)
    dp = [math.inf] * (n + 1)
    back = [-1] * (n + 1)
    dp[0] = 0.0
    for i in range(1, n + 1):
        for j in range(max(0, i - 30), i):
            text = " ".join(str(word["word"]).strip() for word in words[j:i])
            chars = grapheme_len(text)
            duration = float(words[i - 1]["end"]) - float(words[j]["start"])
            if chars > limits["max_chars"] or duration > 7.0:
                if j < i - 1:
                    continue
            gap = 0.0 if i >= n else float(words[i]["start"]) - float(words[i - 1]["end"])
            punctuation_bonus = -2.0 if text.endswith((".", "?", "!")) or gap >= 0.35 else 0.0
            mid_phrase_penalty = 2.0 if gap < 0.05 and punctuation_bonus == 0.0 and i < n else 0.0
            short_penalty = 3.0 if duration < 1.0 else 0.0
            length_cost = ((chars - limits["target"]) ** 2) / limits["target"]
            cost = dp[j] + length_cost + short_penalty + 0.5 + punctuation_bonus + mid_phrase_penalty
            if cost < dp[i]:
                dp[i] = cost
                back[i] = j
    if math.isinf(dp[n]):
        raise ValueError("Unable to segment words under subtitle constraints")
    spans: list[tuple[int, int]] = []
    cursor = n
    while cursor > 0:
        start = back[cursor]
        spans.append((start, cursor))
        cursor = start
    spans.reverse()
    drafts: list[SubtitleSegmentDraft] = []
    for idx, (start, end) in enumerate(spans):
        span = words[start:end]
        confidence = sum(float(word.get("prob", 0.9)) for word in span) / len(span)
        drafts.append(
            SubtitleSegmentDraft(
                idx=idx,
                start_time=float(span[0]["start"]),
                end_time=float(span[-1]["end"]),
                text=" ".join(str(word["word"]).strip() for word in span),
                confidence=confidence,
            )
        )
    return drafts
