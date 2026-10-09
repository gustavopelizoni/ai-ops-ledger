from __future__ import annotations

import json
from typing import Any

from agent.models import SelectedContext
from agent.ollama_client import OllamaClient
from agent.trivy import TrivyScanner
from skills.base_auditor import CategoryAuditor


class SecurityAuditor(CategoryAuditor):
    category = "security"

    def __init__(self, client: OllamaClient, rules: dict[str, Any], schema: dict[str, Any]) -> None:
        super().__init__(client, rules, schema)
        self.trivy_scanner = TrivyScanner()

    def audit(self, context: SelectedContext) -> dict[str, Any]:
        trivy_report = self.trivy_scanner.scan_context(context)
        enriched_text = context.text()
        if trivy_report.get("available") and (
            trivy_report.get("vulnerabilities")
            or trivy_report.get("secrets")
            or trivy_report.get("misconfigurations")
        ):
            enriched_text += (
                "\n\n--- TRIVY SECURITY & GUARDRAIL SCAN RESULTS ---\n"
                f"{json.dumps(trivy_report, ensure_ascii=False, indent=2)}\n"
                "---------------------------------------------\n"
            )

        return self.client.analyze(
            self.category,
            self.rules["categories"][self.category]["rules"],
            enriched_text,
            self.schema,
        )
