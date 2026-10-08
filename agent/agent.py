from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from agent.config import Settings, scope_with_environment
from agent.logging import event
from agent.models import RepositoryTarget
from agent.ollama_client import OllamaClient, OllamaError
from agent.planner import WorkflowPlanner
from agent.scorer import DeterministicScorer
from agent.sdd import SDD
from agent.validator import AuditValidator, ValidationError
from skills.code_analyzer import CodeAnalyzer
from skills.finops_auditor import FinOpsAuditor
from skills.github_collector import GitHubCollector
from skills.observability_auditor import ObservabilityAuditor
from skills.report_generator import ReportGenerator
from skills.resilience_auditor import ResilienceAuditor
from skills.security_auditor import SecurityAuditor


class HermesAuditor:
    """Harness-controlled audit runner. Targets are accepted but never selected here."""

    def __init__(self, settings: Settings, sdd: SDD, logger: Any) -> None:
        self.settings, self.sdd, self.logger = settings, sdd, logger
        self.scope = scope_with_environment(sdd.scope)
        self.planner = WorkflowPlanner(sdd.workflow)
        self.collector = GitHubCollector(settings.github_token, settings.request_timeout_seconds, self.scope)
        self.analyzer = CodeAnalyzer(self.scope)
        self.client = OllamaClient(settings.ollama_host, settings.model, settings.request_timeout_seconds, settings.llm_num_predict)
        self.validator = AuditValidator(sdd.llm_schema, sdd.result_schema)
        self.scorer = DeterministicScorer(sdd.rules)
        self.reporter = ReportGenerator(settings.output_dir)
        self.auditors = (FinOpsAuditor(self.client, sdd.rules, sdd.llm_schema), ResilienceAuditor(self.client, sdd.rules, sdd.llm_schema), SecurityAuditor(self.client, sdd.rules, sdd.llm_schema), ObservabilityAuditor(self.client, sdd.rules, sdd.llm_schema))

    def check_model(self) -> None:
        models = self.client.health().get("models", [])
        names = {model.get("name") for model in models if isinstance(model, dict)}
        if self.settings.model not in names:
            raise OllamaError(f"Configured model '{self.settings.model}' is unavailable. Run: ollama pull {self.settings.model}")

    def audit(self, target: RepositoryTarget) -> dict[str, Any]:
        event(self.logger, "audit_started", repository=target.full_name)
        collected = self.collector.collect(target)
        event(self.logger, "repository_collected", repository=target.full_name, commit=collected.target.commit_sha, file_count=len(collected.files))
        context = self.analyzer.select(collected)
        if not context.files:
            raise RuntimeError("No files matched the configured audit scope")
        event(self.logger, "files_selected", repository=target.full_name, file_count=len(context.files))
        analyses: list[dict[str, Any]] = []
        for auditor in self.auditors:
            for attempt in range(self.settings.max_llm_retries + 1):
                event(self.logger, "skill_started", repository=target.full_name, category=auditor.category, attempt=attempt + 1)
                try:
                    event(self.logger, "llm_request", repository=target.full_name, category=auditor.category)
                    raw = auditor.audit(context)
                    event(self.logger, "llm_response", repository=target.full_name, category=auditor.category)
                    analyses.append(self.validator.validate_analysis(raw, auditor.category, context))
                    event(self.logger, "validation_success", repository=target.full_name, category=auditor.category)
                    break
                except (OllamaError, ValidationError) as error:
                    event(self.logger, "validation_failed", repository=target.full_name, category=auditor.category, attempt=attempt + 1, error=str(error))
                    if attempt == self.settings.max_llm_retries:
                        raise RuntimeError(f"Audit failed for {auditor.category}: {error}") from error
        categories, score, grade, findings = self.scorer.score(analyses)
        summary = " ".join(analysis["summary"] for analysis in analyses)
        result = {
            "repository": {"full_name": collected.target.full_name, "url": collected.target.url, "selection_mode": collected.target.selection_mode},
            "audit": {"score": score, "grade": grade},
            "summary": summary,
            "findings": findings,
            "categories": categories,
            "provenance": {"commit_sha": collected.target.commit_sha, "github_id": collected.target.github_id, "model": self.settings.model, "sdd_hashes": self.sdd.hashes},
            "generated_at": datetime.now(UTC).isoformat(),
        }
        self.validator.validate_result({key: value for key, value in result.items() if key != "generated_at"})
        event(self.logger, "score_calculated", repository=target.full_name, score=score, grade=grade)
        return result

    def publish(self, results: list[dict[str, Any]]) -> None:
        for result in results:
            report = self.reporter.write_report(result)
            event(self.logger, "report_generated", repository=result["repository"]["full_name"], path=str(report))
        index = self.reporter.write_index(results)
        event(self.logger, "audit_completed", reports=len(results), index=str(index))
