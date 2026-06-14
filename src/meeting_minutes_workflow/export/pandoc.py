from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path


Runner = Callable[[list[str]], None]


def run_pandoc_to_docx(
    markdown_file: Path,
    docx_file: Path,
    *,
    reference_doc: Path,
    runner: Runner | None = None,
) -> None:
    docx_file.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "pandoc",
        "--from",
        "gfm",
        "--to",
        "docx",
        "--standalone",
        "--reference-doc",
        str(reference_doc),
        str(markdown_file),
        "--output",
        str(docx_file),
    ]
    if runner is None:
        subprocess.run(command, check=True)
    else:
        runner(command)
    if not docx_file.is_file() or docx_file.stat().st_size == 0:
        raise ValueError(f"Pandoc did not create a non-empty Word file: {docx_file}")


def export_markdown_to_docx(
    markdown_file: Path,
    docx_file: Path,
    *,
    reference_doc: Path | None = None,
    runner: Runner | None = None,
) -> None:
    from meeting_minutes_workflow.export.word import export_markdown_to_word

    export_markdown_to_word(markdown_file, docx_file, reference_doc=reference_doc, runner=runner)


def export_run_markdown_to_docx(run_folder: Path, *, runner: Runner | None = None) -> None:
    from meeting_minutes_workflow.export.word import export_run_markdown_to_word

    export_run_markdown_to_word(run_folder, runner=runner)
