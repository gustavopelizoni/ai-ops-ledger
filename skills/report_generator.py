from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from jinja2 import BaseLoader, Environment, select_autoescape


REPORT_TEMPLATE = """<!doctype html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><script src=\"https://cdn.tailwindcss.com\"></script><title>{{ result.repository.full_name }} · Hermes Auditor</title></head><body class=\"bg-slate-950 text-slate-100\"><main class=\"mx-auto max-w-5xl p-8\"><a class=\"text-cyan-300\" href=\"../index.html\">← Todas as auditorias</a><p class=\"mt-8 text-sm text-slate-400\">Hermes Agentic Auditor · análise estática</p><h1 class=\"text-4xl font-bold\">{{ result.repository.full_name }}</h1><p class=\"mt-2 text-slate-300\">Commit {{ result.provenance.commit_sha }} · {{ result.repository.selection_mode }}</p><section class=\"mt-8 rounded-xl bg-slate-800 p-6\"><span class=\"text-5xl font-bold\">{{ result.audit.score }}</span><span class=\"ml-3 text-2xl\">Nota {{ result.audit.grade }}</span><p class=\"mt-4\">{{ result.summary }}</p></section><section class=\"mt-8 grid gap-4 md:grid-cols-4\">{% for name, category in result.categories.items() %}<article class=\"rounded-lg bg-slate-800 p-4\"><h2 class=\"capitalize\">{{ name }}</h2><p class=\"text-2xl\">{{ category.score }} · {{ category.grade }}</p><p class=\"text-sm text-slate-400\">{{ category.finding_count }} findings</p></article>{% endfor %}</section><section class=\"mt-8\"><h2 class=\"text-2xl font-bold\">Findings</h2>{% for finding in result.findings %}<article class=\"mt-4 rounded-lg border border-slate-700 p-5\"><p class=\"text-sm uppercase text-amber-300\">{{ finding.severity }} · {{ finding.category }}</p><h3 class=\"text-xl font-semibold\">{{ finding.title }}</h3><p class=\"mt-2\">{{ finding.description }}</p><p class=\"mt-2 font-mono text-sm text-cyan-200\">{{ finding.file }}:{{ finding.line }}</p><p class=\"mt-2 text-slate-300\"><strong>Recomendação:</strong> {{ finding.recommendation }}</p></article>{% else %}<p class=\"mt-4\">Nenhum finding validado.</p>{% endfor %}</section></main></body></html>"""
INDEX_TEMPLATE = """<!doctype html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><script src=\"https://cdn.tailwindcss.com\"></script><title>Hermes Agentic Auditor</title></head><body class=\"bg-slate-950 text-slate-100\"><main class=\"mx-auto max-w-5xl p-8\"><p class=\"text-cyan-300\">AI Ops Ledger</p><h1 class=\"text-4xl font-bold\">Hermes Agentic Auditor</h1><p class=\"mt-3 text-slate-300\">Auditorias estáticas, locais e reproduzíveis de projetos de IA.</p><section class=\"mt-8 space-y-3\">{% for report in reports %}<a class=\"block rounded-lg bg-slate-800 p-5 hover:bg-slate-700\" href=\"reports/{{ report.filename }}\"><span class=\"font-semibold\">{{ report.repository.full_name }}</span><span class=\"ml-3\">{{ report.audit.score }} · {{ report.audit.grade }}</span><p class=\"mt-1 text-sm text-slate-400\">{{ report.repository.selection_mode }} · {{ report.findings|length }} findings · {{ report.generated_at }}</p></a>{% else %}<p class=\"rounded-lg bg-slate-800 p-5\">Ainda não há relatórios publicados.</p>{% endfor %}</section></main></body></html>"""


class ReportGenerator:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.environment = Environment(loader=BaseLoader(), autoescape=select_autoescape(default_for_string=True))

    @staticmethod
    def _filename(result: dict[str, Any]) -> str:
        return result["repository"]["full_name"].replace("/", "-").lower() + ".html"

    def write_report(self, result: dict[str, Any]) -> Path:
        reports = self.output_dir / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        filename = self._filename(result)
        (reports / filename).write_text(self.environment.from_string(REPORT_TEMPLATE).render(result=result), encoding="utf-8")
        return reports / filename

    def write_index(self, results: list[dict[str, Any]]) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        catalogue = self.output_dir / "reports.json"
        previous: dict[str, dict[str, Any]] = {}
        if catalogue.is_file():
            try:
                previous = {entry["repository"]["full_name"]: entry for entry in json.loads(catalogue.read_text(encoding="utf-8"))}
            except (json.JSONDecodeError, KeyError, TypeError):
                previous = {}
        for result in results:
            entry = {**result, "filename": self._filename(result), "generated_at": result.get("generated_at", datetime.now(UTC).isoformat())}
            previous[result["repository"]["full_name"]] = entry
        entries = sorted(previous.values(), key=lambda item: item["repository"]["full_name"].lower())
        catalogue.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
        path = self.output_dir / "index.html"
        path.write_text(self.environment.from_string(INDEX_TEMPLATE).render(reports=entries), encoding="utf-8")
        return path
