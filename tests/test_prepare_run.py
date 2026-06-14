from pathlib import Path
import json
import subprocess

import pytest

from meeting_minutes_workflow.doctor import check_readiness
from meeting_minutes_workflow.audio import (
    WHISPERKIT_APPLE_AUDIO_RUNTIME_HINT,
    WHISPERKIT_CACHE_PERMISSION_HINT,
    TranscriptionResult,
)
from meeting_minutes_workflow.audio import transcribe_audio_with_whisperkit
from meeting_minutes_workflow.extractors import extract_transcript_text
from meeting_minutes_workflow.validation import validate_transcript
from meeting_minutes_workflow.workflow import prepare_transcript_run


def test_prepare_transcript_run_extracts_one_text_source(tmp_path: Path) -> None:
    input_folder = tmp_path / "input"
    output_folder = tmp_path / "outputs"
    input_folder.mkdir()
    output_folder.mkdir()
    source = input_folder / "meeting.txt"
    source.write_text("Alice: We agreed the budget review needs a follow-up next week.", encoding="utf-8")

    result = prepare_transcript_run(
        input_folder=input_folder,
        outputs_folder=output_folder,
        meeting_title="Finance Planning",
        run_date="2026-06-12",
    )

    assert result.run_folder == output_folder / "2026-06-12-finance-planning"
    assert (result.run_folder / ".work" / "extracted-transcript.txt").read_text(encoding="utf-8") == source.read_text(
        encoding="utf-8"
    )
    metadata = json.loads((result.run_folder / "run.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "incomplete"
    assert metadata["source"]["filename"] == "meeting.txt"
    assert len(metadata["source"]["sha256"]) == 64


def test_prepare_transcript_run_numbers_duplicate_output_folders(tmp_path: Path) -> None:
    input_folder = tmp_path / "input"
    output_folder = tmp_path / "outputs"
    input_folder.mkdir()
    output_folder.mkdir()
    (input_folder / "meeting.md").write_text("# Transcript\n\nA useful transcript body.", encoding="utf-8")
    (output_folder / "2026-06-12-finance-planning").mkdir()

    result = prepare_transcript_run(
        input_folder=input_folder,
        outputs_folder=output_folder,
        meeting_title="Finance Planning",
        run_date="2026-06-12",
    )

    assert result.run_folder == output_folder / "2026-06-12-finance-planning-2"


def test_prepare_transcript_run_transcribes_one_audio_source(tmp_path: Path) -> None:
    input_folder = tmp_path / "input"
    output_folder = tmp_path / "outputs"
    input_folder.mkdir()
    output_folder.mkdir()
    source = input_folder / "meeting.m4a"
    source.write_bytes(b"fake audio")
    calls: list[tuple[Path, Path]] = []

    def fake_transcriber(source_file: Path, output_file: Path) -> TranscriptionResult:
        calls.append((source_file, output_file))
        output_file.write_text("Alice: Audio transcription worked for this meeting.", encoding="utf-8")
        return TranscriptionResult(
            engine="whisperkit-cli",
            model="large-v3-v20240930_turbo",
            model_path=Path("/Users/example/Library/Application Support/WhisperKit/Models/model"),
            elapsed_seconds=12.3,
        )

    result = prepare_transcript_run(
        input_folder=input_folder,
        outputs_folder=output_folder,
        meeting_title="Audio Planning",
        run_date="2026-06-12",
        audio_transcriber=fake_transcriber,
    )

    extracted_transcript = result.run_folder / ".work" / "extracted-transcript.txt"
    metadata = json.loads((result.run_folder / "run.json").read_text(encoding="utf-8"))
    assert calls == [(source, extracted_transcript)]
    assert extracted_transcript.read_text(encoding="utf-8") == "Alice: Audio transcription worked for this meeting."
    assert not (result.run_folder / "meeting.m4a").exists()
    assert metadata["source"]["filename"] == "meeting.m4a"
    assert metadata["source"]["kind"] == "meeting_recording"
    assert metadata["transcription"]["engine"] == "whisperkit-cli"
    assert metadata["transcription"]["model"] == "large-v3-v20240930_turbo"
    assert metadata["transcription"]["elapsed_seconds"] == 12.3


def test_prepare_transcript_run_records_failed_audio_transcription(tmp_path: Path) -> None:
    input_folder = tmp_path / "input"
    output_folder = tmp_path / "outputs"
    input_folder.mkdir()
    output_folder.mkdir()
    (input_folder / "meeting.m4a").write_bytes(b"fake audio")

    def failing_transcriber(source_file: Path, output_file: Path) -> TranscriptionResult:
        raise ValueError("WhisperKit failed.")

    with pytest.raises(ValueError, match="WhisperKit failed"):
        prepare_transcript_run(
            input_folder=input_folder,
            outputs_folder=output_folder,
            meeting_title="Audio Planning",
            run_date="2026-06-12",
            audio_transcriber=failing_transcriber,
        )

    metadata = json.loads((output_folder / "2026-06-12-audio-planning" / "run.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"
    assert metadata["source"]["kind"] == "meeting_recording"
    assert metadata["generated_files"] == []
    assert metadata["errors"] == ["WhisperKit failed."]


def test_whisperkit_cache_permission_failure_has_actionable_message(tmp_path: Path) -> None:
    source = tmp_path / "meeting.m4a"
    output = tmp_path / "extracted-transcript.txt"
    source.write_bytes(b"fake audio")

    def failing_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(
            134,
            command,
            stderr=(
                "filesystem error: in create_directories: Operation not permitted "
                '["/Users/example/Library/Caches/whisperkit-cli/cache.bundle"]'
            ),
        )

    with pytest.raises(RuntimeError, match="WhisperKit could not write its Apple runtime cache"):
        transcribe_audio_with_whisperkit(source, output, runner=failing_runner)

    assert not output.exists()


def test_whisperkit_cache_permission_failure_is_recorded_in_run_metadata(tmp_path: Path) -> None:
    input_folder = tmp_path / "input"
    output_folder = tmp_path / "outputs"
    input_folder.mkdir()
    output_folder.mkdir()
    source = input_folder / "meeting.m4a"
    source.write_bytes(b"fake audio")

    def failing_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(
            134,
            command,
            stderr=(
                "filesystem error: in create_directories: Operation not permitted "
                '["/Users/example/Library/Caches/whisperkit-cli/cache.bundle"]'
            ),
        )

    def failing_transcriber(source_file: Path, output_file: Path) -> TranscriptionResult:
        return transcribe_audio_with_whisperkit(source_file, output_file, runner=failing_runner)

    with pytest.raises(RuntimeError, match="WhisperKit could not write its Apple runtime cache"):
        prepare_transcript_run(
            input_folder=input_folder,
            outputs_folder=output_folder,
            meeting_title="Audio Planning",
            run_date="2026-06-12",
            audio_transcriber=failing_transcriber,
        )

    metadata = json.loads((output_folder / "2026-06-12-audio-planning" / "run.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"
    assert metadata["errors"] == [WHISPERKIT_CACHE_PERMISSION_HINT]


def test_whisperkit_apple_audio_runtime_failure_has_actionable_message(tmp_path: Path) -> None:
    source = tmp_path / "meeting.m4a"
    output = tmp_path / "extracted-transcript.txt"
    source.write_bytes(b"fake audio")

    def failing_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(
            134,
            command,
            stderr=(
                "IOSurfaceSharedEventAddEventListener failed: 10000003\n"
                "*** Terminating app due to uncaught exception 'com.apple.coreaudio.avfaudio', "
                "reason: 'error 1718449215'\n"
                "4   AVFAudio   -[AVAudioFile setFramePosition:] + 96"
            ),
        )

    with pytest.raises(RuntimeError, match="local Apple audio runtime failure"):
        transcribe_audio_with_whisperkit(source, output, runner=failing_runner)

    assert not output.exists()


def test_whisperkit_apple_audio_runtime_failure_is_recorded_in_run_metadata(tmp_path: Path) -> None:
    input_folder = tmp_path / "input"
    output_folder = tmp_path / "outputs"
    input_folder.mkdir()
    output_folder.mkdir()
    source = input_folder / "meeting.m4a"
    source.write_bytes(b"fake audio")

    def failing_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(
            134,
            command,
            stderr=(
                "IOSurfaceSharedEventAddEventListener failed: 10000003\n"
                "*** Terminating app due to uncaught exception 'com.apple.coreaudio.avfaudio', "
                "reason: 'error 1718449215'"
            ),
        )

    def failing_transcriber(source_file: Path, output_file: Path) -> TranscriptionResult:
        return transcribe_audio_with_whisperkit(source_file, output_file, runner=failing_runner)

    with pytest.raises(RuntimeError, match="local Apple audio runtime failure"):
        prepare_transcript_run(
            input_folder=input_folder,
            outputs_folder=output_folder,
            meeting_title="Audio Planning",
            run_date="2026-06-12",
            audio_transcriber=failing_transcriber,
        )

    metadata = json.loads((output_folder / "2026-06-12-audio-planning" / "run.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"
    assert metadata["errors"] == [WHISPERKIT_APPLE_AUDIO_RUNTIME_HINT]


def test_prepare_transcript_run_requires_exactly_one_source_file(tmp_path: Path) -> None:
    input_folder = tmp_path / "input"
    output_folder = tmp_path / "outputs"
    input_folder.mkdir()
    output_folder.mkdir()
    (input_folder / ".gitkeep").write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected exactly one source file"):
        prepare_transcript_run(
            input_folder=input_folder,
            outputs_folder=output_folder,
            meeting_title="Finance Planning",
            run_date="2026-06-12",
        )


def test_prepare_transcript_run_rejects_unsupported_transcript_format(tmp_path: Path) -> None:
    input_folder = tmp_path / "input"
    output_folder = tmp_path / "outputs"
    input_folder.mkdir()
    output_folder.mkdir()
    (input_folder / "meeting.pdf").write_text("not supported", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported source file extension: .pdf"):
        prepare_transcript_run(
            input_folder=input_folder,
            outputs_folder=output_folder,
            meeting_title="Finance Planning",
            run_date="2026-06-12",
        )


def test_vtt_extraction_removes_timestamps_and_preserves_voice_spans(tmp_path: Path) -> None:
    source = tmp_path / "meeting.vtt"
    source.write_text(
        """WEBVTT

00:00:00.000 --> 00:00:02.000
<v Alice>We need to approve the budget.

00:00:02.000 --> 00:00:04.000
<v Bob><i>Agreed</i>, and I will send the update.
""",
        encoding="utf-8",
    )

    assert extract_transcript_text(source) == "Alice: We need to approve the budget.\n\nBob: Agreed, and I will send the update."


def test_vtt_extraction_removes_rolling_caption_fragments_without_deleting_genuine_repetition(tmp_path: Path) -> None:
    source = tmp_path / "meeting.vtt"
    source.write_text(
        """WEBVTT

00:00:00.000 --> 00:00:03.000
<v Alice>We need

00:00:00.000 --> 00:00:06.000
<v Alice>We need to make sure

00:00:00.000 --> 00:00:09.000
<v Alice>We need to make sure rolling caption fragments do not get counted three times.

00:00:20.000 --> 00:00:24.000
<v Ben>Review notes are essential.

00:00:40.000 --> 00:00:44.000
<v Ben>Review notes are essential.
""",
        encoding="utf-8",
    )

    assert extract_transcript_text(source) == (
        "Alice: We need to make sure rolling caption fragments do not get counted three times.\n\n"
        "Ben: Review notes are essential.\n\n"
        "Ben: Review notes are essential."
    )


def test_transcript_validation_requires_at_least_ten_words() -> None:
    with pytest.raises(ValueError, match="at least 10 words"):
        validate_transcript("# Transcript\n\nToo short.")


def test_doctor_reports_transcript_ready_separately_from_word_export() -> None:
    readiness = check_readiness()

    assert readiness["transcript_workflow"].ready is True
    assert "pandoc" in readiness["word_export"].detail.lower()


def test_doctor_reports_audio_ready_when_whisperkit_and_model_are_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import meeting_minutes_workflow.setup_readiness as setup_readiness

    model_path = tmp_path / "openai_whisper-large-v3-v20240930_turbo"
    model_path.mkdir()
    monkeypatch.setattr(setup_readiness, "WHISPERKIT_MODEL_PATH", model_path)
    monkeypatch.setattr(setup_readiness.shutil, "which", lambda name: f"/fake/bin/{name}")

    readiness = setup_readiness.check_workflow_readiness()

    assert readiness["audio_transcription"].ready is True
    assert "WhisperKit CLI found" in readiness["audio_transcription"].detail
