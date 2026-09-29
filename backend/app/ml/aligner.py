def cleanup_words(words: list[dict], offset: float = 0.0) -> list[dict]:
    cleaned: list[dict] = []
    previous_end = 0.0
    for raw in sorted(words, key=lambda item: (float(item["start"]) + offset, float(item["end"]) + offset)):
        text = str(raw.get("word", "")).strip()
        if not text:
            continue
        start = max(previous_end, float(raw["start"]) + offset)
        end = max(start + 0.01, float(raw["end"]) + offset)
        prob = float(raw.get("prob", raw.get("probability", 0.9)))
        cleaned.append({"word": text, "start": start, "end": end, "prob": max(0.0, min(1.0, prob))})
        previous_end = end
    return cleaned
