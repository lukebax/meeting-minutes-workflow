from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass

from meeting_minutes_workflow.audio import WHISPERKIT_MODEL_PATH


@dataclass(frozen=True)
class Readiness:
    ready: bool
    detail: str
    label: str


def check_workflow_readiness() -> dict[str, Readiness]:
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
        "python_environment": Readiness(True, "Python environment is available.", "Python environment"),
        "transcript_workflow": Readiness(True, "Transcript workflow helpers are available.", "Transcript workflow"),
        "audio_transcription": Readiness(audio_ready, audio_detail, "Audio transcription"),
        "word_export": Readiness(
            pandoc_path is not None,
            f"Pandoc found at {pandoc_path}." if pandoc_path else "Pandoc not found; Word export is not ready.",
            "Word export",
        ),
    }


def check_setup_readiness() -> dict[str, Readiness]:
    checks = {
        "apple_silicon_mac": _check_apple_silicon(),
        "homebrew": _check_homebrew(),
        "pandoc": _check_tool("pandoc", "Word export"),
        "whisperkit_cli": _check_tool("whisperkit-cli", "meeting recording transcription"),
        "whisperkit_model": _check_whisperkit_model(),
    }
    return checks


def setup_guidance(checks: dict[str, Readiness]) -> list[str]:
    missing = {label for label, check in checks.items() if not check.ready}
    guidance: list[str] = []
    if "homebrew" in missing:
        guidance.append(
            "Homebrew is missing. Codex should ask before installing Homebrew or ask the user to install it."
        )
    elif "pandoc" in missing or "whisperkit_cli" in missing:
        commands = []
        if "pandoc" in missing:
            commands.append("pandoc")
        if "whisperkit_cli" in missing:
            commands.append("whisperkit-cli")
        guidance.append(f"Codex should ask before running: brew install {' '.join(commands)}")
    if "whisperkit_model" in missing:
        guidance.append(
            "WhisperKit model is missing. Codex should ask before preparing or downloading the Large v3 Turbo model."
        )
    return guidance


def _check_apple_silicon() -> Readiness:
    machine = platform.machine()
    system = platform.system()
    if system == "Darwin" and machine == "arm64":
        return Readiness(True, "Local audio transcription is supported.", "Apple Silicon Mac")
    return Readiness(
        False,
        f"Detected {system} {machine}; transcript workflows can still work, "
        "but v1 audio support expects Apple Silicon.",
        "Apple Silicon Mac",
    )


def _check_homebrew() -> Readiness:
    brew_path = shutil.which("brew")
    if brew_path:
        return Readiness(True, f"Found at {brew_path}.", "Homebrew")
    return Readiness(False, "Not found. Pandoc and WhisperKit CLI are normally installed with Homebrew.", "Homebrew")


def _check_tool(command: str, purpose: str) -> Readiness:
    path = shutil.which(command)
    if path:
        return Readiness(True, f"Found at {path}.", _tool_label(command))
    return Readiness(False, f"Not found. Required for {purpose}.", _tool_label(command))


def _check_whisperkit_model() -> Readiness:
    if WHISPERKIT_MODEL_PATH.is_dir():
        return Readiness(True, f"Found at {WHISPERKIT_MODEL_PATH}.", "WhisperKit model")
    return Readiness(False, f"Not found at {WHISPERKIT_MODEL_PATH}.", "WhisperKit model")


def _tool_label(command: str) -> str:
    return {
        "pandoc": "Pandoc",
        "whisperkit-cli": "WhisperKit CLI",
    }.get(command, command)
