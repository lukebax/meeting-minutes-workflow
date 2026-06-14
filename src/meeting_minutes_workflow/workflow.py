from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from meeting_minutes_workflow.audio import transcribe_audio_with_whisperkit
from meeting_minutes_workflow.source_material import AudioTranscriber, find_source_material
from meeting_minutes_workflow.workflow_run import WorkflowRun


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
    audio_transcriber: AudioTranscriber = transcribe_audio_with_whisperkit,
) -> PreparedRun:
    source = find_source_material(input_folder)
    run = WorkflowRun.create(outputs_folder=outputs_folder, run_date=run_date, meeting_title=meeting_title)
    run.prepare_source_material(
        source,
        meeting_title=meeting_title,
        run_date=run_date,
        audio_transcriber=audio_transcriber,
    )
    return PreparedRun(run_folder=run.path, source_file=source.path)
