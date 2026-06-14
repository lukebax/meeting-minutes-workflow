from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from meeting_minutes_workflow.doctor import check_readiness
from meeting_minutes_workflow.workflow import prepare_transcript_run
from meeting_minutes_workflow.workflow_run import WorkflowStage, run_workflow_stage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="meeting-minutes")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor")
    prepare_parser = subparsers.add_parser("prepare-run")
    prepare_parser.add_argument("--input-folder", type=Path, default=Path("input"))
    prepare_parser.add_argument("--outputs-folder", type=Path, default=Path("outputs"))
    prepare_parser.add_argument("--title", required=True)
    prepare_parser.add_argument("--run-date", default=date.today().isoformat())
    validate_transcript_parser = subparsers.add_parser("validate-transcript")
    validate_transcript_parser.add_argument("run_folder", type=Path)
    validate_markdown_parser = subparsers.add_parser("validate-markdown")
    validate_markdown_parser.add_argument("run_folder", type=Path)
    export_docx_parser = subparsers.add_parser("export-docx")
    export_docx_parser.add_argument("run_folder", type=Path)
    assemble_parser = subparsers.add_parser("assemble-combined")
    assemble_parser.add_argument("run_folder", type=Path)
    finish_parser = subparsers.add_parser("finish-run")
    finish_parser.add_argument("run_folder", type=Path)
    args = parser.parse_args(argv)
    if args.command == "doctor":
        for readiness in check_readiness().values():
            status = "ready" if readiness.ready else "not ready"
            print(f"{readiness.label}: {status} - {readiness.detail}")
        return 0
    if args.command == "prepare-run":
        try:
            result = prepare_transcript_run(
                input_folder=args.input_folder,
                outputs_folder=args.outputs_folder,
                meeting_title=args.title,
                run_date=args.run_date,
            )
        except Exception as error:
            print(f"Error: {error}")
            return 1
        print(result.run_folder)
        return 0
    if args.command == "validate-transcript":
        return _run_stage(args.run_folder, WorkflowStage.VALIDATE_TRANSCRIPT)
    if args.command == "validate-markdown":
        return _run_stage(args.run_folder, WorkflowStage.VALIDATE_MARKDOWN)
    if args.command == "export-docx":
        return _run_stage(args.run_folder, WorkflowStage.EXPORT_DOCX)
    if args.command == "assemble-combined":
        return _run_stage(args.run_folder, WorkflowStage.ASSEMBLE_COMBINED)
    if args.command == "finish-run":
        return _run_stage(args.run_folder, WorkflowStage.FINISH_RUN)
    return 0


def _run_stage(run_folder: Path, stage: WorkflowStage) -> int:
    try:
        success_message = run_workflow_stage(run_folder, stage)
    except Exception as error:
        print(f"Error: {error}")
        return 1
    print(success_message)
    return 0
