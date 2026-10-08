from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SDD:
    rules: dict[str, Any]
    scope: dict[str, Any]
    workflow: dict[str, Any]
    llm_schema: dict[str, Any]
    result_schema: dict[str, Any]
    hashes: dict[str, str]


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        value = yaml.safe_load(source)
    if not isinstance(value, dict):
        raise ValueError(f"Invalid SDD document: {path}")
    return value


def load_sdd(root: Path) -> SDD:
    directory = root / "specs"
    paths = {
        "rules": directory / "audit_rules.yaml",
        "scope": directory / "audit_scope.yaml",
        "workflow": directory / "audit_workflow.yaml",
        "llm_schema": directory / "llm_analysis_schema.json",
        "result_schema": directory / "audit_schema.json",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing SDD files: {', '.join(missing)}")
    rules, scope, workflow = (_read_yaml(paths[key]) for key in ("rules", "scope", "workflow"))
    with paths["llm_schema"].open(encoding="utf-8") as source:
        llm_schema = json.load(source)
    with paths["result_schema"].open(encoding="utf-8") as source:
        result_schema = json.load(source)
    categories = set(rules.get("categories", {}))
    if categories != {"finops", "resilience", "security", "architecture"}:
        raise ValueError("audit_rules.yaml must define the four MVP categories")
    if abs(sum(rules["scoring"]["weights"].values()) - 1) > 0.0001:
        raise ValueError("Scoring weights must total 1")
    return SDD(
        rules=rules,
        scope=scope,
        workflow=workflow,
        llm_schema=llm_schema,
        result_schema=result_schema,
        hashes={key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items()},
    )
