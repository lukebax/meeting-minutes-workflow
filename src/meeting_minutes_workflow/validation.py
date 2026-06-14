from __future__ import annotations

import re
import shutil
import subprocess
import zipfile
from pathlib import Path


EXPECTED_MARKDOWN_OUTPUTS = [
    "transcript.md",
    "overview.md",
    "minutes.md",
    "actions.md",
    "decisions.md",
    "combined.md",
]

EXPECTED_DOCX_OUTPUTS = [filename.replace(".md", ".docx") for filename in EXPECTED_MARKDOWN_OUTPUTS]


def validate_transcript(markdown_text: str, *, minimum_words: int = 10) -> None:
    words = re.findall(r"\b[\w'-]+\b", markdown_text)
    if len(words) < minimum_words:
        raise ValueError(f"Transcript must contain at least {minimum_words} words.")


def validate_markdown_outputs(markdown_folder: Path) -> None:
    missing_or_empty = [
        filename
        for filename in EXPECTED_MARKDOWN_OUTPUTS
        if not (markdown_folder / filename).is_file()
        or not (markdown_folder / filename).read_text(encoding="utf-8").strip()
    ]
    if missing_or_empty:
        raise ValueError(f"Expected non-empty Markdown outputs: {', '.join(missing_or_empty)}")


def validate_docx_outputs(docx_folder: Path) -> None:
    missing_or_empty = [
        filename
        for filename in EXPECTED_DOCX_OUTPUTS
        if not (docx_folder / filename).is_file() or (docx_folder / filename).stat().st_size == 0
    ]
    if missing_or_empty:
        raise ValueError(f"Expected non-empty Word outputs: {', '.join(missing_or_empty)}")

    unreadable_packages = [
        filename
        for filename in EXPECTED_DOCX_OUTPUTS
        if not zipfile.is_zipfile(docx_folder / filename)
    ]
    if unreadable_packages:
        raise ValueError(f"Expected valid Word packages: {', '.join(unreadable_packages)}")

    pandoc = shutil.which("pandoc")
    if pandoc is None:
        return

    unreadable_by_pandoc: list[str] = []
    for filename in EXPECTED_DOCX_OUTPUTS:
        docx_file = docx_folder / filename
        result = subprocess.run(
            [pandoc, "--from", "docx", "--to", "plain", str(docx_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            message = result.stderr.strip() or "Pandoc could not read the file."
            unreadable_by_pandoc.append(f"{filename} ({message})")

    if unreadable_by_pandoc:
        raise ValueError(f"Expected Pandoc-readable Word outputs: {', '.join(unreadable_by_pandoc)}")
