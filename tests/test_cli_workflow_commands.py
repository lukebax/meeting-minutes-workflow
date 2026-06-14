from __future__ import annotations

import json
import stat
import zipfile
from pathlib import Path

import pytest

from meeting_minutes_workflow.cli import main
from meeting_minutes_workflow.validation import EXPECTED_DOCX_OUTPUTS, EXPECTED_MARKDOWN_OUTPUTS, validate_docx_outputs


def test_cli_validate_transcript_accepts_canonical_transcript(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run_folder = _make_run_folder(tmp_path)
    transcript = run_folder / "markdown" / "transcript.md"
    transcript.write_text(
        "# Finance Planning Transcript\n\nAlice: This transcript has enough words to pass the validation check.",
        encoding="utf-8",
    )

    exit_code = main(["validate-transcript", str(run_folder)])

    assert exit_code == 0
    assert "Transcript is valid" in capsys.readouterr().out


def test_cli_validate_transcript_failure_updates_run_metadata(tmp_path: Path) -> None:
    run_folder = _make_run_folder(tmp_path)
    (run_folder / "markdown" / "transcript.md").write_text("# Transcript\n\nToo short.", encoding="utf-8")

    exit_code = main(["validate-transcript", str(run_folder)])

    metadata = json.loads((run_folder / "run.json").read_text(encoding="utf-8"))
    assert exit_code == 1
    assert metadata["status"] == "failed"
    assert "at least 10 words" in metadata["errors"][0]


def test_cli_validate_markdown_requires_all_summary_outputs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run_folder = _make_run_folder(tmp_path)
    for filename in EXPECTED_MARKDOWN_OUTPUTS:
        (run_folder / "markdown" / filename).write_text(f"# {filename}\n\nReady.", encoding="utf-8")

    exit_code = main(["validate-markdown", str(run_folder)])

    assert exit_code == 0
    assert "Markdown outputs are valid" in capsys.readouterr().out


def test_cli_export_docx_exports_all_markdown_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_folder = _make_run_folder(tmp_path)
    for filename in EXPECTED_MARKDOWN_OUTPUTS:
        (run_folder / "markdown" / filename).write_text(f"# {filename}\n\nReady.", encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_source_docx = tmp_path / "fake-source.docx"
    _write_docx_with_four_column_table(fake_source_docx)
    fake_bin.mkdir()
    fake_pandoc = fake_bin / "pandoc"
    fake_pandoc.write_text(
        f"""#!/bin/sh
if [ "$1" = "--from" ] && [ "$2" = "docx" ]; then
  exit 0
fi
while [ "$1" != "" ]; do
  if [ "$1" = "--output" ]; then
    shift
    /bin/cp "{fake_source_docx}" "$1"
    exit 0
  fi
  shift
done
exit 1
""",
        encoding="utf-8",
    )
    fake_pandoc.chmod(fake_pandoc.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(fake_bin))

    exit_code = main(["export-docx", str(run_folder)])

    assert exit_code == 0
    for filename in EXPECTED_MARKDOWN_OUTPUTS:
        docx_file = run_folder / "docx" / filename.replace(".md", ".docx")
        assert zipfile.is_zipfile(docx_file)
        assert docx_file.stat().st_size > 0


def test_cli_assemble_combined_copies_sections_from_separate_outputs(tmp_path: Path) -> None:
    run_folder = _make_run_folder(tmp_path)
    (run_folder / "markdown" / "overview.md").write_text("# Finance Planning - Overview\n\nOverview body.", encoding="utf-8")
    (run_folder / "markdown" / "minutes.md").write_text(
        "# Finance Planning - Minutes\n\n## Informal Discussion\n\nInformal body.",
        encoding="utf-8",
    )
    (run_folder / "markdown" / "actions.md").write_text("# Finance Planning - Actions\n\nActions body.", encoding="utf-8")
    (run_folder / "markdown" / "decisions.md").write_text("# Finance Planning - Decisions\n\nDecisions body.", encoding="utf-8")

    exit_code = main(["assemble-combined", str(run_folder)])

    combined = (run_folder / "markdown" / "combined.md").read_text(encoding="utf-8")
    assert exit_code == 0
    assert combined == (
        "# Finance Planning - Combined Output\n\n"
        "## Overview\n\nOverview body.\n\n"
        "## Minutes\n\n### Informal Discussion\n\nInformal body.\n\n"
        "## Actions\n\nActions body.\n\n"
        "## Decisions\n\nDecisions body.\n"
    )


def test_cli_finish_run_records_success_and_generated_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_folder = _make_run_folder(tmp_path)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_pandoc = fake_bin / "pandoc"
    fake_pandoc.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_pandoc.chmod(fake_pandoc.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(fake_bin))
    for filename in EXPECTED_MARKDOWN_OUTPUTS:
        (run_folder / "markdown" / filename).write_text(f"# {filename}\n\nReady.", encoding="utf-8")
        _write_docx_with_four_column_table(run_folder / "docx" / filename.replace(".md", ".docx"))

    exit_code = main(["finish-run", str(run_folder)])

    metadata = json.loads((run_folder / "run.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert metadata["status"] == "success"
    assert "markdown/transcript.md" in metadata["generated_files"]
    assert "docx/combined.docx" in metadata["generated_files"]


def test_export_docx_uses_reference_docx_for_table_formatting(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from meeting_minutes_workflow.export.word import export_run_markdown_to_word

    run_folder = _make_run_folder(tmp_path)
    for filename in EXPECTED_MARKDOWN_OUTPUTS:
        (run_folder / "markdown" / filename).write_text(f"# {filename}\n\nReady.", encoding="utf-8")
    commands: list[list[str]] = []

    def fake_runner(command: list[str]) -> None:
        commands.append(command)
        output_path = Path(command[command.index("--output") + 1])
        _write_docx_with_four_column_table(output_path)

    export_run_markdown_to_word(run_folder, runner=fake_runner)

    assert all("--reference-doc" in command for command in commands)


def test_docx_table_optimisation_sets_action_table_column_widths(tmp_path: Path) -> None:
    from meeting_minutes_workflow.export.docx_tables import ACTION_TABLE_WIDTHS, optimise_docx_tables

    docx_file = tmp_path / "actions.docx"
    _write_docx_with_four_column_table(docx_file)

    optimise_docx_tables(docx_file)

    document_xml = _read_docx_document_xml(docx_file)
    assert [f'w="{width}"' in document_xml for width in ACTION_TABLE_WIDTHS] == [True, True, True, True]


def test_docx_optimisation_normalises_bullet_numbering(tmp_path: Path) -> None:
    from meeting_minutes_workflow.export.docx_tables import optimise_docx_tables

    docx_file = tmp_path / "bullets.docx"
    _write_docx_with_symbol_bullets(docx_file)

    optimise_docx_tables(docx_file)

    document_xml = _read_docx_document_xml(docx_file)
    numbering_xml = _read_docx_numbering_xml(docx_file)
    assert "• " in document_xml
    assert "numPr" not in document_xml
    assert 'val="•"' in numbering_xml
    assert 'ascii="Arial"' in numbering_xml
    assert 'val="\uf0b7"' not in numbering_xml


def test_docx_optimisation_preserves_word_namespace_prefix(tmp_path: Path) -> None:
    from meeting_minutes_workflow.export.docx_tables import optimise_docx_tables

    docx_file = tmp_path / "bullets.docx"
    _write_docx_with_symbol_bullets(docx_file)

    optimise_docx_tables(docx_file)

    document_xml = _read_docx_document_xml(docx_file)
    numbering_xml = _read_docx_numbering_xml(docx_file)
    assert "<w:document" in document_xml
    assert "<w:numbering" in numbering_xml
    assert "ns0:" not in document_xml
    assert "ns0:" not in numbering_xml


def test_docx_validation_rejects_pandoc_unreadable_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    docx_folder = tmp_path / "docx"
    fake_bin = tmp_path / "bin"
    docx_folder.mkdir()
    fake_bin.mkdir()
    fake_pandoc = fake_bin / "pandoc"
    fake_pandoc.write_text("#!/bin/sh\nprintf 'could not read docx\\n' >&2\nexit 63\n", encoding="utf-8")
    fake_pandoc.chmod(fake_pandoc.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(fake_bin))
    for filename in EXPECTED_DOCX_OUTPUTS:
        _write_docx_with_four_column_table(docx_folder / filename)

    with pytest.raises(ValueError, match="Pandoc-readable Word outputs"):
        validate_docx_outputs(docx_folder)


def _make_run_folder(tmp_path: Path) -> Path:
    run_folder = tmp_path / "outputs" / "2026-06-13-finance-planning"
    (run_folder / "markdown").mkdir(parents=True)
    (run_folder / "docx").mkdir()
    (run_folder / ".work").mkdir()
    (run_folder / "run.json").write_text(
        json.dumps(
            {
                "meeting_title": "Finance Planning",
                "run_date": "2026-06-13",
                "status": "incomplete",
                "generated_files": [".work/extracted-transcript.txt"],
                "errors": [],
            }
        ),
        encoding="utf-8",
    )
    return run_folder


def _write_docx_with_four_column_table(path: Path) -> None:
    document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:tbl>
      <w:tblPr><w:tblW w:type="auto" w:w="0"/></w:tblPr>
      <w:tblGrid><w:gridCol w:w="1980"/><w:gridCol w:w="1980"/><w:gridCol w:w="1980"/><w:gridCol w:w="1980"/></w:tblGrid>
      <w:tr>
        <w:tc><w:tcPr/><w:p><w:r><w:t>Action</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr/><w:p><w:r><w:t>Owner</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr/><w:p><w:r><w:t>Due date</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr/><w:p><w:r><w:t>Review note</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>
"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "")
        archive.writestr("word/document.xml", document_xml)


def _write_docx_with_symbol_bullets(path: Path) -> None:
    document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1001"/></w:numPr></w:pPr><w:r><w:t>Bullet item</w:t></w:r></w:p>
  </w:body>
</w:document>
"""
    numbering_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:abstractNum w:abstractNumId="991">
    <w:lvl w:ilvl="0">
      <w:numFmt w:val="bullet"/>
      <w:lvlText w:val="&#61623;"/>
      <w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol" w:cs="Symbol"/></w:rPr>
    </w:lvl>
  </w:abstractNum>
  <w:num w:numId="1001"><w:abstractNumId w:val="991"/></w:num>
</w:numbering>
"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "")
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/numbering.xml", numbering_xml)


def _read_docx_document_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read("word/document.xml").decode("utf-8")


def _read_docx_numbering_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read("word/numbering.xml").decode("utf-8")
