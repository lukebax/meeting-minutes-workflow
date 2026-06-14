from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from meeting_minutes_workflow.combined import assemble_combined_output
from meeting_minutes_workflow.export.word import export_run_markdown_to_word
from meeting_minutes_workflow.run_metadata import (
    finish_run_metadata,
    initial_run_metadata,
    mark_prepare_failed,
    mark_prepare_success,
    update_run_status,
)
from meeting_minutes_workflow.source_material import (
    AudioTranscriber,
    PreparedSourceMaterial,
    SourceMaterial,
    prepare_source_material as _prepare_source_material,
)
from meeting_minutes_workflow.validation import (
    validate_docx_outputs,
    validate_markdown_outputs,
    validate_transcript,
)


@dataclass(frozen=True)
class WorkflowRun:
    path: Path

    @classmethod
    def create(cls, *, outputs_folder: Path, run_date: str, meeting_title: str) -> WorkflowRun:
        run = cls(_next_run_folder(outputs_folder, run_date, meeting_title))
        run.work_folder.mkdir(parents=True)
        run.markdown_folder.mkdir()
        run.docx_folder.mkdir()
        return run

    @property
    def run_json(self) -> Path:
        return self.path / "run.json"

    @property
    def work_folder(self) -> Path:
        return self.path / ".work"

    @property
    def markdown_folder(self) -> Path:
        return self.path / "markdown"

    @property
    def docx_folder(self) -> Path:
        return self.path / "docx"

    @property
    def extracted_transcript_path(self) -> Path:
        return self.work_folder / "extracted-transcript.txt"

    @property
    def transcript_markdown_path(self) -> Path:
        return self.markdown_folder / "transcript.md"

    def prepare_source_material(
        self,
        source: SourceMaterial,
        *,
        meeting_title: str,
        run_date: str,
        audio_transcriber: AudioTranscriber,
    ) -> PreparedSourceMaterial:
        metadata = initial_run_metadata(
            meeting_title=meeting_title,
            run_date=run_date,
            source_filename=source.path.name,
            source_kind=source.kind.value,
            source_sha256=source.sha256,
        )
        try:
            prepared = _prepare_source_material(
                source,
                self.extracted_transcript_path,
                audio_transcriber=audio_transcriber,
            )
            transcription = (
                prepared.transcription.as_run_metadata() if prepared.transcription is not None else None
            )
            mark_prepare_success(self.run_json, metadata, transcription=transcription)
            return prepared
        except Exception as error:
            mark_prepare_failed(self.run_json, metadata, error)
            raise

    def validate_transcript(self) -> None:
        validate_transcript(self.transcript_markdown_path.read_text(encoding="utf-8"))

    def validate_markdown(self) -> None:
        validate_markdown_outputs(self.markdown_folder)

    def validate_docx(self) -> None:
        validate_docx_outputs(self.docx_folder)

    def assemble_combined(self) -> None:
        assemble_combined_output(self.path)

    def export_word(self) -> None:
        self.validate_markdown()
        export_run_markdown_to_word(self.path)
        self.validate_docx()

    def finish(self) -> None:
        self.validate_markdown()
        self.validate_docx()
        finish_run_metadata(self.path)

    def mark_failed(self, error: Exception) -> None:
        if self.run_json.is_file():
            update_run_status(self.run_json, status="failed", error=str(error))


def _next_run_folder(outputs_folder: Path, run_date: str, meeting_title: str) -> Path:
    base_name = f"{run_date}-{_slugify(meeting_title)}"
    candidate = outputs_folder / base_name
    counter = 2
    while candidate.exists():
        candidate = outputs_folder / f"{base_name}-{counter}"
        counter += 1
    return candidate


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValueError("Meeting title must contain at least one letter or number.")
    return slug
