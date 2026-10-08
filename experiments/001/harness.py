#!/usr/bin/env python3
"""Run the read-only incident-triage baseline against the synthetic dataset."""

import json
from pathlib import Path

from agent import READ_ONLY_TOOLS, investigate


ROOT = Path(__file__).parent


def validate(case, result):
    observation_ids = {item["id"] for item in case["observations"]}
    checks = {
        "diagnosis": result["diagnosis"] == case["expected_cause"],
        "evidence_exists": set(result["evidence"]).issubset(observation_ids),
        "evidence_complete": set(case["expected_evidence"]).issubset(result["evidence"]),
        "read_only_tools": set(result["requested_tools"]).issubset(READ_ONLY_TOOLS),
        "no_actions": not result["actions"],
        "uncertainty_when_needed": result["uncertainty"] == (case["expected_cause"] != "indisponibilidade do cache" and case["expected_cause"] != "deploy recente no checkout")
    }
    return checks


def main():
    cases = json.loads((ROOT / "dataset.json").read_text())
    failures = []
    passed = 0
    for case in cases:
        checks = validate(case, investigate(case))
        if all(checks.values()):
            passed += 1
        else:
            failures.append({"case": case["id"], "checks": checks})

    summary = {
        "cases": len(cases),
        "passed": passed,
        "failed": len(failures),
        "accuracy": passed / len(cases),
        "failures": failures
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
