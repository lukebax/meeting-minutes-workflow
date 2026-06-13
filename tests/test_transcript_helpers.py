from __future__ import annotations

import json
import stat
import sys
import types
import zipfile
from pathlib import Path

import pytest

from meeting_minutes_workflow.cli import main
from meeting_minutes_workflow.export.pandoc import export_markdown_to_docx
from meeting_minutes_workflow.extractors import extract_transcript_text
from meeting_minutes_workflow.run_metadata import update_run_status
from meeting_minutes_workflow.validation import validate_markdown_outputs


def test_run_metadata_status_can_be_updated(tmp_path: Path) -> None:
    run_json = tmp_path / "run.json"
    run_json.write_text(json.dumps({"status": "incomplete", "errors": []}), encoding="utf-8")

    update_run_status(run_json, status="failed", error="Transcript is too short.")

    metadata = json.loads(run_json.read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"
    assert metadata["errors"] == ["Transcript is too short."]


def test_markdown_validation_requires_expected_outputs(tmp_path: Path) -> None:
    markdown_folder = tmp_path / "markdown"
    markdown_folder.mkdir()
    for filename in ["transcript.md", "overview.md", "minutes.md", "actions.md", "decisions.md", "combined.md"]:
        (markdown_folder / filename).write_text(f"# {filename}\n\nReady.", encoding="utf-8")

    validate_markdown_outputs(markdown_folder)

    (markdown_folder / "actions.md").write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="actions.md"):
        validate_markdown_outputs(markdown_folder)


def test_pandoc_export_writes_docx_using_runner(tmp_path: Path) -> None:
    markdown_file = tmp_path / "transcript.md"
    docx_file = tmp_path / "transcript.docx"
    markdown_file.write_text("# Transcript\n\nReady for export.", encoding="utf-8")

    def fake_runner(command: list[str]) -> None:
        assert command[:5] == ["pandoc", "--from", "gfm", "--to", "docx"]
        assert command[-2:] == ["--output", str(docx_file)]
        _write_minimal_docx(docx_file, ["Ready for export."])

    export_markdown_to_docx(markdown_file, docx_file, runner=fake_runner)

    assert zipfile.is_zipfile(docx_file)


def test_docx_extraction_reads_paragraph_text(tmp_path: Path) -> None:
    source = tmp_path / "meeting.docx"
    _write_minimal_docx(source, ["Alice opened the meeting.", "Bob agreed to send the notes."])

    assert extract_transcript_text(source) == "Alice opened the meeting.\n\nBob agreed to send the notes."


def test_docx_extraction_prefers_mammoth_when_available(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "meeting.docx"
    source.write_bytes(b"fake docx bytes")
    calls: list[bytes] = []

    def extract_raw_text(handle: object) -> object:
        calls.append(handle.read())
        return types.SimpleNamespace(value="Alice opened the meeting with Mammoth.\n")

    monkeypatch.setitem(sys.modules, "mammoth", types.SimpleNamespace(extract_raw_text=extract_raw_text))

    assert extract_transcript_text(source) == "Alice opened the meeting with Mammoth."
    assert calls == [b"fake docx bytes"]


def test_cli_doctor_reports_readiness(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["doctor"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Transcript workflow:" in output
    assert "Word export:" in output


def test_cli_prepare_run_creates_transcript_work_area(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_folder = tmp_path / "input"
    outputs_folder = tmp_path / "outputs"
    input_folder.mkdir()
    outputs_folder.mkdir()
    (input_folder / "meeting.txt").write_text("Alice confirmed the plan and Bob noted the action.", encoding="utf-8")

    exit_code = main(
        [
            "prepare-run",
            "--input-folder",
            str(input_folder),
            "--outputs-folder",
            str(outputs_folder),
            "--title",
            "Finance Planning",
            "--run-date",
            "2026-06-12",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert str(outputs_folder / "2026-06-12-finance-planning") in output
    assert (outputs_folder / "2026-06-12-finance-planning" / ".work" / "extracted-transcript.txt").is_file()


def test_cli_prepare_run_transcribes_audio_with_whisperkit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_folder = tmp_path / "input"
    outputs_folder = tmp_path / "outputs"
    fake_bin = tmp_path / "bin"
    input_folder.mkdir()
    outputs_folder.mkdir()
    fake_bin.mkdir()
    (input_folder / "meeting.m4a").write_bytes(b"fake audio")
    fake_whisperkit = fake_bin / "whisperkit-cli"
    fake_whisperkit.write_text(
        """#!/bin/sh
printf 'Alice: The audio helper produced a transcript.\\n'
""",
        encoding="utf-8",
    )
    fake_whisperkit.chmod(fake_whisperkit.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(fake_bin))

    exit_code = main(
        [
            "prepare-run",
            "--input-folder",
            str(input_folder),
            "--outputs-folder",
            str(outputs_folder),
            "--title",
            "Audio Planning",
            "--run-date",
            "2026-06-12",
        ]
    )

    run_folder = outputs_folder / "2026-06-12-audio-planning"
    metadata = json.loads((run_folder / "run.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert (run_folder / ".work" / "extracted-transcript.txt").read_text(encoding="utf-8") == (
        "Alice: The audio helper produced a transcript.\n"
    )
    assert metadata["source"]["kind"] == "meeting_recording"
    assert metadata["transcription"]["engine"] == "whisperkit-cli"
    assert metadata["transcription"]["model"] == "large-v3-v20240930_turbo"


def test_cli_prepare_run_reports_prepare_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_folder = tmp_path / "input"
    outputs_folder = tmp_path / "outputs"
    input_folder.mkdir()
    outputs_folder.mkdir()
    (input_folder / "meeting.pdf").write_text("not supported", encoding="utf-8")

    exit_code = main(
        [
            "prepare-run",
            "--input-folder",
            str(input_folder),
            "--outputs-folder",
            str(outputs_folder),
            "--title",
            "Audio Planning",
            "--run-date",
            "2026-06-12",
        ]
    )

    assert exit_code == 1
    assert "Error: Unsupported source file extension: .pdf" in capsys.readouterr().out


def _write_minimal_docx(path: Path, paragraphs: list[str]) -> None:
    paragraph_xml = "".join(
        f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"
        for text in paragraphs
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{paragraph_xml}</w:body>"
        "</w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
