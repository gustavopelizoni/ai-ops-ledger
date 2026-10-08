from __future__ import annotations

from typing import Any

from agent.models import SelectedContext
from agent.ollama_client import OllamaClient


class CategoryAuditor:
    category: str

    def __init__(self, client: OllamaClient, rules: dict[str, Any], schema: dict[str, Any]) -> None:
        self.client, self.rules, self.schema = client, rules, schema

    def audit(self, context: SelectedContext) -> dict[str, Any]:
        return self.client.analyze(self.category, self.rules["categories"][self.category]["rules"], context.text(), self.schema)
