from pathlib import Path

import pytest

from agent.models import SelectedContext, SelectedFile
from agent.scorer import DeterministicScorer
from agent.sdd import load_sdd
from agent.validator import AuditValidator, ValidationError


def finding(severity="high"):
    return {"category": "security", "severity": severity, "title": "Unsafe input", "description": "Input reaches a command path.", "file": "agent.py", "line": 2, "recommendation": "Validate it."}


def test_validator_rejects_unknown_source_location():
    sdd = load_sdd(Path("."))
    validator = AuditValidator(sdd.llm_schema, sdd.result_schema)
    analysis = {"category": "security", "summary": "x", "findings": [finding()]}
    context = SelectedContext([SelectedFile("agent.py", "one", 1, 1)])
    with pytest.raises(ValidationError):
        validator.validate_analysis(analysis, "security", context)


def test_validator_rejects_placeholder_recommendation():
    sdd = load_sdd(Path("."))
    validator = AuditValidator(sdd.llm_schema, sdd.result_schema)
    analysis = {"category": "security", "summary": "x", "findings": [{**finding(), "line": 1, "recommendation": "None"}]}
    context = SelectedContext([SelectedFile("agent.py", "one", 1, 1)])
    with pytest.raises(ValidationError, match="recommendation"):
        validator.validate_analysis(analysis, "security", context)


def test_scorer_uses_sdd_penalties_and_weights():
    sdd = load_sdd(Path("."))
    analyses = [{"category": category, "summary": "ok", "findings": [finding()] if category == "security" else []} for category in sdd.rules["categories"]]
    categories, score, grade, findings = DeterministicScorer(sdd.rules).score(analyses)
    assert categories["security"]["score"] == 75
    assert score == 92.5
    assert grade == "A"
    assert findings == [finding()]
