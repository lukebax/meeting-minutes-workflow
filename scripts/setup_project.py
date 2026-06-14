#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from meeting_minutes_workflow.first_time_setup import run_first_time_setup  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare the meeting minutes workflow for Codex use.")
    parser.add_argument(
        "--skip-python-install",
        action="store_true",
        help="Check setup without creating .venv or installing Python dependencies.",
    )
    args = parser.parse_args(argv)

    return run_first_time_setup(REPO_ROOT, skip_python_install=args.skip_python_install)


if __name__ == "__main__":
    raise SystemExit(main())
