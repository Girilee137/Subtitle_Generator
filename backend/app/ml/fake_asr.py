from app.core.config import SUPPORTED_LANGUAGES


def transcribe_fake(language: str) -> list[dict]:
    if language not in SUPPORTED_LANGUAGES:
        language = "en"
    if language == "ta":
        words = [
            ("வணக்கம்", 0.0, 0.6, 0.96),
            ("இது", 0.7, 1.0, 0.93),
            ("ஒரு", 1.1, 1.4, 0.91),
            ("சோதனை.", 1.5, 2.2, 0.95),
        ]
    else:
        words = [
            ("Hello", 0.0, 0.4, 0.98),
            ("this", 0.5, 0.8, 0.96),
            ("is", 0.9, 1.0, 0.97),
            ("a", 1.1, 1.2, 0.95),
            ("test.", 1.3, 1.8, 0.98),
        ]
    return [{"word": word, "start": start, "end": end, "prob": prob} for word, start, end, prob in words]
