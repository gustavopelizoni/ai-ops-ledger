from __future__ import annotations

from typing import Any


class WorkflowPlanner:
    """Validates the declarative SDD workflow; it does not execute arbitrary YAML."""

    REQUIRED = ("SELECT", "DISCOVER_OR_VALIDATE", "COLLECT", "ANALYZE", "AUDIT", "VALIDATE", "SCORE", "REPORT")

    def __init__(self, workflow: dict[str, Any]) -> None:
        stages = workflow.get("stages", [])
        names = tuple(stage.get("name") for stage in stages if isinstance(stage, dict))
        if names != self.REQUIRED:
            raise ValueError(f"Invalid workflow stages: expected {self.REQUIRED}, received {names}")
        self.stages = stages
