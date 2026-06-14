from __future__ import annotations

import json
from pathlib import Path


def initial_run_metadata(
    *,
    meeting_title: str,
    run_date: str,
    source_filename: str,
    source_kind: str,
    source_sha256: str,
) -> dict[str, object]:
    return {
        "meeting_title": meeting_title,
        "run_date": run_date,
        "status": "incomplete",
        "source": {
            "filename": source_filename,
            "kind": source_kind,
            "sha256": source_sha256,
        },
        "generated_files": [],
        "errors": [],
    }


def write_run_metadata(run_json: Path, metadata: dict[str, object]) -> None:
    run_json.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def mark_prepare_success(
    run_json: Path,
    metadata: dict[str, object],
    *,
    transcription: dict[str, object] | None = None,
) -> None:
    metadata["generated_files"] = [".work/extracted-transcript.txt"]
    if transcription is not None:
        metadata["transcription"] = transcription
    write_run_metadata(run_json, metadata)


def mark_prepare_failed(run_json: Path, metadata: dict[str, object], error: Exception) -> None:
    metadata["status"] = "failed"
    metadata["errors"] = [str(error)]
    write_run_metadata(run_json, metadata)


def update_run_status(run_json: Path, *, status: str, error: str | None = None) -> None:
    metadata = json.loads(run_json.read_text(encoding="utf-8"))
    metadata["status"] = status
    errors = list(metadata.get("errors", []))
    if error:
        errors.append(error)
    metadata["errors"] = errors
    write_run_metadata(run_json, metadata)


def finish_run_metadata(run_folder: Path) -> None:
    run_json = run_folder / "run.json"
    metadata = json.loads(run_json.read_text(encoding="utf-8"))
    generated_files = sorted(
        str(path.relative_to(run_folder))
        for folder in [run_folder / "markdown", run_folder / "docx"]
        for path in folder.iterdir()
        if path.is_file()
    )
    existing_files = [item for item in metadata.get("generated_files", []) if item not in generated_files]
    metadata["generated_files"] = existing_files + generated_files
    metadata["status"] = "success"
    metadata["errors"] = []
    write_run_metadata(run_json, metadata)
