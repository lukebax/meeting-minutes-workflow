from __future__ import annotations

from pathlib import Path

from meeting_minutes_workflow.combined import assemble_combined_output
from meeting_minutes_workflow.export.pandoc import export_run_markdown_to_docx
from meeting_minutes_workflow.run_metadata import finish_run_metadata, update_run_status
from meeting_minutes_workflow.validation import (
    validate_docx_outputs,
    validate_markdown_outputs,
    validate_transcript,
)


def validate_run_transcript(run_folder: Path) -> None:
    transcript_path = run_folder / "markdown" / "transcript.md"
    validate_transcript(transcript_path.read_text(encoding="utf-8"))


def validate_run_markdown(run_folder: Path) -> None:
    validate_markdown_outputs(run_folder / "markdown")


def assemble_run_combined(run_folder: Path) -> None:
    assemble_combined_output(run_folder)


def export_run_docx(run_folder: Path) -> None:
    validate_run_markdown(run_folder)
    export_run_markdown_to_docx(run_folder)
    validate_docx_outputs(run_folder / "docx")


def finish_run(run_folder: Path) -> None:
    validate_run_markdown(run_folder)
    validate_docx_outputs(run_folder / "docx")
    finish_run_metadata(run_folder)


def mark_run_failed(run_folder: Path, error: Exception) -> None:
    run_json = run_folder / "run.json"
    if run_json.is_file():
        update_run_status(run_json, status="failed", error=str(error))
