from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

from agent.models import SelectedContext


class ValidationError(ValueError):
    pass


class AuditValidator:
    def __init__(self, llm_schema: dict[str, Any], result_schema: dict[str, Any]) -> None:
        self.llm_validator = Draft202012Validator(llm_schema)
        self.result_validator = Draft202012Validator(result_schema)

    @staticmethod
    def _errors(validator: Draft202012Validator, value: dict[str, Any]) -> str:
        return "; ".join(error.message for error in validator.iter_errors(value))

    def validate_analysis(self, analysis: dict[str, Any], expected_category: str, context: SelectedContext) -> dict[str, Any]:
        errors = self._errors(self.llm_validator, analysis)
        if errors:
            raise ValidationError(f"LLM schema validation failed: {errors}")
        if analysis["category"] != expected_category:
            raise ValidationError("LLM response category does not match requested category")
        line_counts = context.line_counts()
        for finding in analysis["findings"]:
            if finding["category"] != expected_category:
                raise ValidationError("Finding category does not match requested category")
            maximum = line_counts.get(finding["file"])
            if maximum is None or finding["line"] > maximum:
                raise ValidationError(f"Finding has unverifiable location: {finding['file']}:{finding['line']}")
            if finding["recommendation"].strip().lower() in {"none", "n/a", "na", "not applicable", "no recommendation"}:
                raise ValidationError("Finding recommendation must be concrete and actionable")
        return analysis

    def validate_result(self, result: dict[str, Any]) -> dict[str, Any]:
        errors = self._errors(self.result_validator, result)
        if errors:
            raise ValidationError(f"Audit result schema validation failed: {errors}")
        return result
