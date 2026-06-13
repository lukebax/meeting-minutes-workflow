from __future__ import annotations

import json
from pathlib import Path


def update_run_status(run_json: Path, *, status: str, error: str | None = None) -> None:
    metadata = json.loads(run_json.read_text(encoding="utf-8"))
    metadata["status"] = status
    errors = list(metadata.get("errors", []))
    if error:
        errors.append(error)
    metadata["errors"] = errors
    run_json.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    run_json.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
