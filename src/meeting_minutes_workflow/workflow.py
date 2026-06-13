from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from meeting_minutes_workflow.extractors import SUPPORTED_TRANSCRIPT_EXTENSIONS, extract_transcript_text


@dataclass(frozen=True)
class PreparedRun:
    run_folder: Path
    source_file: Path


def prepare_transcript_run(
    *,
    input_folder: Path,
    outputs_folder: Path,
    meeting_title: str,
    run_date: str,
) -> PreparedRun:
    source_file = _find_one_source_file(input_folder)
    run_folder = _next_run_folder(outputs_folder, run_date, meeting_title)
    work_folder = run_folder / ".work"
    markdown_folder = run_folder / "markdown"
    docx_folder = run_folder / "docx"
    work_folder.mkdir(parents=True)
    markdown_folder.mkdir()
    docx_folder.mkdir()

    extracted_text = extract_transcript_text(source_file)
    (work_folder / "extracted-transcript.txt").write_text(extracted_text, encoding="utf-8")
    _write_run_metadata(
        run_folder / "run.json",
        {
            "meeting_title": meeting_title,
            "run_date": run_date,
            "status": "incomplete",
            "source": {
                "filename": source_file.name,
                "sha256": _sha256(source_file),
            },
            "generated_files": [
                ".work/extracted-transcript.txt",
            ],
            "errors": [],
        },
    )
    return PreparedRun(run_folder=run_folder, source_file=source_file)


def _find_one_source_file(input_folder: Path) -> Path:
    source_files = sorted(
        path
        for path in input_folder.iterdir()
        if path.is_file() and path.name != ".gitkeep" and not path.name.startswith(".")
    )
    if len(source_files) != 1:
        raise ValueError(f"Expected exactly one source file in {input_folder}, found {len(source_files)}.")
    source_file = source_files[0]
    if source_file.suffix.lower() not in SUPPORTED_TRANSCRIPT_EXTENSIONS:
        raise ValueError(f"Unsupported source file extension: {source_file.suffix}")
    return source_file


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_run_metadata(path: Path, metadata: dict[str, object]) -> None:
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
