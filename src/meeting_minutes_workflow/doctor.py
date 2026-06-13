from __future__ import annotations

import shutil
from dataclasses import dataclass

from meeting_minutes_workflow.audio import WHISPERKIT_MODEL_PATH


@dataclass(frozen=True)
class Readiness:
    ready: bool
    detail: str


def check_readiness() -> dict[str, Readiness]:
    pandoc_path = shutil.which("pandoc")
    whisperkit_path = shutil.which("whisperkit-cli")
    audio_ready = whisperkit_path is not None and WHISPERKIT_MODEL_PATH.is_dir()
    if audio_ready:
        audio_detail = f"WhisperKit CLI found at {whisperkit_path}; model found at {WHISPERKIT_MODEL_PATH}."
    elif whisperkit_path is None:
        audio_detail = "WhisperKit CLI not found; audio transcription is not ready."
    else:
        audio_detail = f"WhisperKit CLI found at {whisperkit_path}; model not found at {WHISPERKIT_MODEL_PATH}."
    return {
        "python_environment": Readiness(True, "Python environment is available."),
        "transcript_workflow": Readiness(True, "Transcript workflow helpers are available."),
        "audio_transcription": Readiness(audio_ready, audio_detail),
        "word_export": Readiness(
            pandoc_path is not None,
            f"Pandoc found at {pandoc_path}." if pandoc_path else "Pandoc not found; Word export is not ready.",
        ),
    }
