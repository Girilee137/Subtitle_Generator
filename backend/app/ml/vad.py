def detect_speech_intervals(audio_path: str, duration_seconds: float | None = None) -> list[tuple[float, float]]:
    if duration_seconds and duration_seconds > 0:
        return [(0.0, duration_seconds)]
    return [(0.0, 30.0)]
