from __future__ import annotations

import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class Readiness:
    ready: bool
    detail: str


def check_readiness() -> dict[str, Readiness]:
    pandoc_path = shutil.which("pandoc")
    return {
        "python_environment": Readiness(True, "Python environment is available."),
        "transcript_workflow": Readiness(True, "Transcript workflow helpers are available."),
        "audio_transcription": Readiness(False, "Audio transcription is not implemented yet."),
        "word_export": Readiness(
            pandoc_path is not None,
            f"Pandoc found at {pandoc_path}." if pandoc_path else "Pandoc not found; Word export is not ready.",
        ),
    }
