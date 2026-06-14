from __future__ import annotations

from meeting_minutes_workflow.setup_readiness import Readiness, check_workflow_readiness


def check_readiness() -> dict[str, Readiness]:
    return check_workflow_readiness()
