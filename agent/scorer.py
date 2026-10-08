from __future__ import annotations

from typing import Any


class DeterministicScorer:
    def __init__(self, rules: dict[str, Any]) -> None:
        self.scoring = rules["scoring"]
        self.categories = tuple(rules["categories"])

    def grade(self, score: float) -> str:
        for threshold in self.scoring["grades"]:
            if score >= threshold["minimum"]:
                return threshold["grade"]
        return "F"

    def score(self, analyses: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], float, str, list[dict[str, Any]]]:
        by_category = {category: [] for category in self.categories}
        summaries: list[str] = []
        seen: set[tuple[str, str, str, int]] = set()
        findings: list[dict[str, Any]] = []
        for analysis in analyses:
            summaries.append(analysis["summary"])
            for finding in analysis["findings"]:
                identity = (finding["category"], finding["title"], finding["file"], finding["line"])
                if identity not in seen:
                    seen.add(identity)
                    by_category[finding["category"]].append(finding)
                    findings.append(finding)
        categories: dict[str, dict[str, Any]] = {}
        total = 0.0
        for category in self.categories:
            score = max(0, 100 - sum(self.scoring["penalties"][finding["severity"]] for finding in by_category[category]))
            categories[category] = {"score": score, "grade": self.grade(score), "finding_count": len(by_category[category])}
            total += score * self.scoring["weights"][category]
        final = round(total, 2)
        return categories, final, self.grade(final), findings
