from __future__ import annotations

import re
from typing import Any

from agent.models import CollectedRepository, SelectedContext, SelectedFile


SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*([:=])\s*(['\"]?)[^\s,'\"]+\3"),
    re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----"),
]


def redact_secrets(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(lambda match: f"{match.group(1)}{match.group(2)}<REDACTED>" if match.lastindex and match.lastindex >= 2 else "<REDACTED_PRIVATE_KEY>", text)
    return text


class CodeAnalyzer:
    def __init__(self, scope: dict[str, Any]) -> None:
        self.scope = scope

    def select(self, repository: CollectedRepository) -> SelectedContext:
        limits = self.scope["limits"]
        priority_names = set(self.scope.get("selection_priority", {}).get("filenames", []))
        keywords = self.scope.get("selection_priority", {}).get("path_keywords", [])
        ranked = []
        for item in repository.files:
            score = 0
            lowered = item.path.lower()
            if item.path.rsplit("/", 1)[-1] in priority_names:
                score += 100
            score += sum(10 for keyword in keywords if keyword in lowered)
            if item.path.endswith(".py"):
                score += 5
            ranked.append((score, item.path, item))
        selected: list[SelectedFile] = []
        context_chars = 0
        for score, _, item in sorted(ranked, key=lambda value: (-value[0], value[1])):
            if len(selected) >= int(limits["max_files"]):
                break
            content = redact_secrets(item.content)
            remaining = int(limits["max_context_chars"]) - context_chars
            if remaining <= 0:
                break
            content = content[:remaining]
            if not content:
                continue
            selected.append(SelectedFile(path=item.path, content=content, line_count=content.count("\n") + 1, score=score))
            context_chars += len(content)
        dependencies = self._dependencies(repository)
        return SelectedContext(files=selected, dependencies=dependencies)

    @staticmethod
    def _dependencies(repository: CollectedRepository) -> list[str]:
        names = {file.path.rsplit("/", 1)[-1]: file.content for file in repository.files}
        output: list[str] = []
        for filename in ("requirements.txt", "pyproject.toml", "package.json"):
            if filename in names:
                output.append(filename)
        return output
