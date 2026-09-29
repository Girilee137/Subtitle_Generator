import asyncio
from pathlib import Path

from app.core.errors import BadRequestError


async def extract_audio(input_path: str, output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        output_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        stderr_text = stderr.decode("utf-8", errors="ignore")
        if "Output file does not contain any stream" in stderr_text:
            raise BadRequestError("The uploaded file does not contain an audio track.", "NO_AUDIO_TRACK")
        raise BadRequestError(f"ffmpeg failed: {stderr_text}", "AUDIO_EXTRACT_FAILED")
