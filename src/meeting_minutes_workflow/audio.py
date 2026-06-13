from __future__ import annotations

import subprocess
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_AUDIO_EXTENSIONS = {".m4a", ".mp3", ".wav", ".flac"}
WHISPERKIT_ENGINE = "whisperkit-cli"
WHISPERKIT_MODEL = "large-v3-v20240930_turbo"
WHISPERKIT_MODEL_PATH = (
    Path.home()
    / "Library"
    / "Application Support"
    / "WhisperKit"
    / "Models"
    / "models"
    / "argmaxinc"
    / "whisperkit-coreml"
    / "openai_whisper-large-v3-v20240930_turbo"
)
WHISPERKIT_MODEL_DOWNLOAD_FOLDER = Path.home() / "Library" / "Application Support" / "WhisperKit" / "Models"

Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class TranscriptionResult:
    engine: str
    model: str
    model_path: Path
    elapsed_seconds: float


def transcribe_audio_with_whisperkit(
    source_file: Path,
    output_file: Path,
    *,
    runner: Runner | None = None,
    model_path: Path = WHISPERKIT_MODEL_PATH,
    model: str = WHISPERKIT_MODEL,
    timer: Callable[[], float] = time.perf_counter,
) -> TranscriptionResult:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    start = timer()
    command = _whisperkit_command(source_file, model_path=model_path, model=model)
    completed = (runner or _run_command)(command)
    transcript = completed.stdout.strip()
    if not transcript:
        raise ValueError("WhisperKit transcription produced no transcript text.")
    output_file.write_text(transcript + "\n", encoding="utf-8")
    return TranscriptionResult(
        engine=WHISPERKIT_ENGINE,
        model=model,
        model_path=model_path,
        elapsed_seconds=round(timer() - start, 3),
    )


def _whisperkit_command(source_file: Path, *, model_path: Path, model: str) -> list[str]:
    command = [
        WHISPERKIT_ENGINE,
        "transcribe",
        "--audio-path",
        str(source_file),
        "--language",
        "en",
    ]
    if model_path.exists():
        command.extend(["--model-path", str(model_path)])
    else:
        command.extend(
            [
                "--model",
                model,
                "--download-model-path",
                str(WHISPERKIT_MODEL_DOWNLOAD_FOLDER),
            ]
        )
    return command


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    print("Transcribing audio with WhisperKit. Long recordings may take a few minutes...")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stdout_file, tempfile.TemporaryFile(
        mode="w+", encoding="utf-8"
    ) as stderr_file:
        process = subprocess.Popen(command, stdout=stdout_file, stderr=stderr_file, text=True)
        start = time.monotonic()
        last_reported = 0
        while process.poll() is None:
            elapsed = int(time.monotonic() - start)
            if elapsed >= last_reported + 30:
                print(f"Still transcribing audio... elapsed {elapsed}s")
                last_reported = elapsed
            time.sleep(1)
        process.wait()
        stdout_file.seek(0)
        stdout = stdout_file.read()
        stderr_file.seek(0)
        stderr = stderr_file.read()
    completed = subprocess.CompletedProcess(command, process.returncode, stdout=stdout, stderr=stderr)
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(completed.returncode, command, output=stdout, stderr=stderr)
    return completed
