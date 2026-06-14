from __future__ import annotations

from pathlib import Path

from meeting_minutes_workflow.workflow_run import WorkflowRun


def validate_run_transcript(run_folder: Path) -> None:
    WorkflowRun(run_folder).validate_transcript()


def validate_run_markdown(run_folder: Path) -> None:
    WorkflowRun(run_folder).validate_markdown()


def assemble_run_combined(run_folder: Path) -> None:
    WorkflowRun(run_folder).assemble_combined()


def export_run_docx(run_folder: Path) -> None:
    WorkflowRun(run_folder).export_word()


def finish_run(run_folder: Path) -> None:
    WorkflowRun(run_folder).finish()


def mark_run_failed(run_folder: Path, error: Exception) -> None:
    WorkflowRun(run_folder).mark_failed(error)
