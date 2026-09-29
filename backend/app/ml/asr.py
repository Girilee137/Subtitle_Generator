"""
ASR module – server-side transcription using faster-whisper.

Each chunk is physically extracted from the audio with ffmpeg before being
passed to the model so that whisper processes only the relevant audio window.
Timestamps from the model are then offset by chunk start_s to produce
absolute times. This prevents the repeated-segment bug that occurs when the
full file is passed and results are merely filtered by time.
"""

import asyncio
import tempfile
from pathlib import Path

from app.core.config import get_settings
from app.ml.cache import cache_key, get_cached_words, set_cached_words
from app.ml.fake_asr import transcribe_fake

_model = None


def load_model():
    global _model
    if _model is not None:
        return _model
    from faster_whisper import WhisperModel

    settings = get_settings()
    device = "cuda"
    compute_type = "float16"
    if settings.whisper_device == "cpu":
        device = "cpu"
        compute_type = "int8"
    elif settings.whisper_device == "auto":
        try:
            import torch
            if not torch.cuda.is_available():
                device = "cpu"
                compute_type = "int8"
        except Exception:
            device = "cpu"
            compute_type = "int8"
    _model = WhisperModel(settings.whisper_model, device=device, compute_type=compute_type)
    return _model


async def _extract_clip(audio_path: str, start_s: float, end_s: float, out_path: str) -> None:
    """Use ffmpeg to extract a precise time window from the audio file."""
    duration = max(0.05, end_s - start_s)
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y",
        "-ss", str(start_s),
        "-i", audio_path,
        "-t", str(duration),
        "-ac", "1", "-ar", "16000", "-f", "wav",
        out_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg clip extraction failed: {stderr.decode(errors='replace')}")


async def transcribe_chunk(
    audio_path: str,
    language: str,
    start_s: float = 0.0,
    end_s: float | None = None,
) -> list[dict]:
    """Transcribe a specific audio window and return word-level timestamps.

    The clip is physically extracted with ffmpeg so faster-whisper only sees
    the relevant audio — this prevents the whole-file repetition bug.
    Timestamps returned are absolute (offset by start_s).

    Args:
        audio_path: Path to the full 16 kHz mono WAV file.
        language:   ISO code 'en' or 'ta'.
        start_s:    Clip start offset in seconds.
        end_s:      Clip end offset in seconds (None = to end of file).

    Returns:
        List of dicts: {word, start, end, prob} with absolute timestamps.
    """
    settings = get_settings()
    if settings.fake_asr:
        return transcribe_fake(language)

    # If no time window is specified, transcribe the full file directly
    if start_s == 0.0 and end_s is None:
        return await _transcribe_path(audio_path, language, offset=0.0)

    # Physically cut the clip so whisper only sees this window
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        clip_path = tmp.name
    try:
        await _extract_clip(audio_path, start_s, end_s or 0.0, clip_path)
        return await _transcribe_path(clip_path, language, offset=start_s)
    finally:
        Path(clip_path).unlink(missing_ok=True)


async def _transcribe_path(audio_path: str, language: str, offset: float) -> list[dict]:
    """Run faster-whisper on the given file and return words offset by `offset` seconds."""
    settings = get_settings()
    pcm = Path(audio_path).read_bytes()
    key = cache_key(pcm, settings.whisper_model, language)
    cached = await get_cached_words(key)
    if cached is not None:
        return cached

    model = load_model()

    def _run():
        segs, _ = model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True,
            vad_filter=False,
            beam_size=5,
            condition_on_previous_text=False,
            no_repeat_ngram_size=5,
        )
        words = []
        for seg in segs:
            for w in seg.words or []:
                text = w.word.strip()
                if not text:
                    continue
                words.append({
                    "word": text,
                    "start": round(w.start + offset, 3),
                    "end": round(w.end + offset, 3),
                    "prob": w.probability,
                })
        return words

    words = await asyncio.to_thread(_run)
    await set_cached_words(key, words)
    return words
