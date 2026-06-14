from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from meeting_minutes_workflow.setup_readiness import Readiness, check_setup_readiness, setup_guidance


def run_first_time_setup(repo_root: Path, *, skip_python_install: bool = False) -> int:
    checks = check_setup_readiness()

    print_setup_checks("System checks", checks)
    print_system_guidance(checks)

    venv_python = _venv_python(repo_root)
    if skip_python_install and not venv_python.is_file():
        print("\nPython environment: .venv is missing. Rerun without --skip-python-install.", flush=True)
        return 1

    if not skip_python_install:
        _ensure_venv(repo_root)
        _install_python_dependencies(repo_root)

    doctor_ok = _run_optional([str(venv_python), "-m", "meeting_minutes_workflow", "doctor"], cwd=repo_root)
    tests_ok = _run_optional([str(venv_python), "-m", "pytest"], cwd=repo_root)
    if doctor_ok and tests_ok:
        print("\nSetup check complete: transcript workflows are ready. Audio and Word readiness are shown above.")
        return 0

    print("\nSetup check completed with issues. Review the messages above before running the workflow.")
    return 1


def print_setup_checks(title: str, checks: dict[str, Readiness]) -> None:
    print(title, flush=True)
    for check in checks.values():
        status = "ready" if check.ready else "not ready"
        print(f"- {check.label}: {status} - {check.detail}", flush=True)


def print_system_guidance(checks: dict[str, Readiness]) -> None:
    guidance = setup_guidance(checks)
    if not guidance:
        return

    print("\nSystem tool guidance", flush=True)
    for item in guidance:
        print(f"- {item}", flush=True)


def _ensure_venv(repo_root: Path) -> None:
    venv_dir = repo_root / ".venv"
    if _venv_python(repo_root).is_file():
        print(f"\nPython environment: using existing {venv_dir}", flush=True)
        return
    print(f"\nPython environment: creating {venv_dir}", flush=True)
    _run([sys.executable, "-m", "venv", str(venv_dir)], cwd=repo_root)


def _install_python_dependencies(repo_root: Path) -> None:
    python = _venv_python(repo_root)
    print("\nPython dependencies: installing project and test dependencies", flush=True)
    _run([str(python), "-m", "pip", "install", "--upgrade", "pip"], cwd=repo_root)
    _run([str(python), "-m", "pip", "install", "-e", ".[dev]"], cwd=repo_root)


def _venv_python(repo_root: Path) -> Path:
    return repo_root / ".venv" / "bin" / "python"


def _run(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def _run_optional(command: list[str], *, cwd: Path) -> bool:
    print(f"\nRunning: {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=cwd)
    return completed.returncode == 0
