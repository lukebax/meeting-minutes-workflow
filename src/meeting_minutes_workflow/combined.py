from __future__ import annotations

import re
from pathlib import Path


COMBINED_PARTS = [
    ("overview.md", "Overview"),
    ("minutes.md", "Minutes"),
    ("actions.md", "Actions"),
    ("decisions.md", "Decisions"),
]


def assemble_combined_output(run_folder: Path) -> Path:
    markdown_folder = run_folder / "markdown"
    title = _combined_title(run_folder)
    sections = [title]
    for filename, heading in COMBINED_PARTS:
        body = _demote_headings(_without_first_heading((markdown_folder / filename).read_text(encoding="utf-8")))
        sections.append(f"## {heading}\n\n{body}".rstrip())
    combined = "\n\n".join(sections) + "\n"
    output_path = markdown_folder / "combined.md"
    output_path.write_text(combined, encoding="utf-8")
    return output_path


def _combined_title(run_folder: Path) -> str:
    overview = (run_folder / "markdown" / "overview.md").read_text(encoding="utf-8")
    first_line = overview.splitlines()[0].lstrip("#").strip()
    meeting_title = re.sub(r"\s+-\s+Overview$", "", first_line)
    return f"# {meeting_title} - Combined Output"


def _without_first_heading(markdown: str) -> str:
    lines = markdown.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def _demote_headings(markdown: str) -> str:
    lines = []
    for line in markdown.splitlines():
        if line.startswith("#"):
            lines.append(f"#{line}")
        else:
            lines.append(line)
    return "\n".join(lines)
