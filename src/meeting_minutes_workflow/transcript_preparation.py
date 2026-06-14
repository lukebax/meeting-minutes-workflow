from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from meeting_minutes_workflow.audio import (
    SUPPORTED_AUDIO_EXTENSIONS,
    TranscriptionResult,
    transcribe_audio_with_whisperkit,
)
from meeting_minutes_workflow.extractors import SUPPORTED_TRANSCRIPT_EXTENSIONS, extract_transcript_text


class SourceKind(StrEnum):
    TRANSCRIPT = "transcript"
    MEETING_RECORDING = "meeting_recording"


@dataclass(frozen=True)
class TranscriptionMetadata:
    engine: str
    model: str
    model_path: Path
    elapsed_seconds: float

    def as_run_metadata(self) -> dict[str, object]:
        return {
            "engine": self.engine,
            "model": self.model,
            "model_path": str(self.model_path),
            "elapsed_seconds": self.elapsed_seconds,
        }


@dataclass(frozen=True)
class SourceMaterial:
    path: Path
    kind: SourceKind
    sha256: str


@dataclass(frozen=True)
class PreparedTranscript:
    source: SourceMaterial
    transcription: TranscriptionMetadata | None


AudioTranscriber = Callable[[Path, Path], TranscriptionResult]


def find_source_material(input_folder: Path) -> SourceMaterial:
    source_files = sorted(
        path
        for path in input_folder.iterdir()
        if path.is_file() and path.name != ".gitkeep" and not path.name.startswith(".")
    )
    if len(source_files) != 1:
        raise ValueError(f"Expected exactly one source file in {input_folder}, found {len(source_files)}.")

    source_file = source_files[0]
    extension = source_file.suffix.lower()
    if extension not in SUPPORTED_TRANSCRIPT_EXTENSIONS | SUPPORTED_AUDIO_EXTENSIONS:
        raise ValueError(f"Unsupported source file extension: {source_file.suffix}")

    return SourceMaterial(
        path=source_file,
        kind=SourceKind.MEETING_RECORDING if extension in SUPPORTED_AUDIO_EXTENSIONS else SourceKind.TRANSCRIPT,
        sha256=_sha256(source_file),
    )


def prepare_transcript(
    source: SourceMaterial,
    extracted_transcript_path: Path,
    *,
    audio_transcriber: AudioTranscriber = transcribe_audio_with_whisperkit,
) -> PreparedTranscript:
    if source.kind == SourceKind.MEETING_RECORDING:
        transcription_result = audio_transcriber(source.path, extracted_transcript_path)
        transcription = TranscriptionMetadata(
            engine=transcription_result.engine,
            model=transcription_result.model,
            model_path=transcription_result.model_path,
            elapsed_seconds=transcription_result.elapsed_seconds,
        )
    else:
        extracted_text = extract_transcript_text(source.path)
        extracted_transcript_path.write_text(extracted_text, encoding="utf-8")
        transcription = None
    return PreparedTranscript(source=source, transcription=transcription)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
