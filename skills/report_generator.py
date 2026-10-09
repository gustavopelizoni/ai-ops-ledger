from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from jinja2 import BaseLoader, Environment, select_autoescape


REPORT_TEMPLATE = """<!doctype html>
<html lang="pt-BR" class="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            slate: {
              950: '#020617',
              900: '#0f172a',
              800: '#1e293b',
              700: '#334155',
            }
          }
        }
      }
    }
  </script>
  <title>{{ result.repository.full_name }} · Hermes Agentic Auditor</title>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen antialiased selection:bg-cyan-500 selection:text-slate-950">
  <header class="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-50">
    <div class="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
      <a class="text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-2 transition" href="../index.html">
        <span>←</span> Voltar para Visão Geral
      </a>
      <div class="text-xs text-slate-400 flex items-center gap-2">
        <span>🛡️</span> Hermes Agentic Auditor · Análise Estática & Segurança Local (Ollama)
      </div>
    </div>
  </header>

  <main class="mx-auto max-w-6xl px-6 py-10 space-y-10">
    <!-- Repository Title & Metadata -->
    <section class="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-slate-900/80 border border-slate-800 rounded-2xl p-8 shadow-xl">
      <div>
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 text-xs font-semibold uppercase tracking-wider bg-cyan-950 text-cyan-300 rounded-full border border-cyan-800/50">
            Modo: {{ result.repository.selection_mode | replace('explicit', 'Explícito') | replace('discovery', 'Descoberta') }}
          </span>
          <span class="text-xs text-slate-400 font-mono">Commit: {{ result.provenance.commit_sha[:10] if result.provenance and result.provenance.commit_sha else 'N/A' }}</span>
        </div>
        <h1 class="text-3xl md:text-4xl font-extrabold mt-3 tracking-tight">
          {% if result.repository.url %}
            <a href="{{ result.repository.url }}" target="_blank" class="hover:text-cyan-400 transition inline-flex items-center gap-2">
              {{ result.repository.full_name }} ↗
            </a>
          {% else %}
            {{ result.repository.full_name }}
          {% endif %}
        </h1>
        <p class="text-sm text-slate-400 mt-2">Relatório de auditoria gerado em {{ result.generated_at | replace('T', ' ') | truncate(19, True, '') if result.generated_at else 'recentemente' }} UTC</p>
      </div>

      <!-- Score & Grade Card -->
      <div class="flex items-center gap-6 bg-slate-950/60 border border-slate-800/80 rounded-xl p-6 shadow-inner">
        <div class="text-center">
          <div class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Score Global</div>
          <div class="text-5xl font-black mt-1 {% if result.audit.score >= 90 %}text-emerald-400{% elif result.audit.score >= 75 %}text-cyan-400{% elif result.audit.score >= 60 %}text-amber-400{% else %}text-rose-400{% endif %}">
            {{ result.audit.score }}
          </div>
        </div>
        <div class="h-12 w-px bg-slate-800"></div>
        <div class="text-center">
          <div class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Nota</div>
          <div class="text-5xl font-black mt-1 {% if result.audit.grade == 'A' %}text-emerald-400{% elif result.audit.grade == 'B' %}text-cyan-400{% elif result.audit.grade == 'C' %}text-amber-400{% else %}text-rose-400{% endif %}">
            {{ result.audit.grade }}
          </div>
        </div>
      </div>
    </section>

    <!-- Executive Summary -->
    <section class="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 shadow-lg">
      <h2 class="text-xl font-bold text-slate-200 flex items-center gap-2 mb-4">
        <span>💡</span> Resumo Executivo e Insights de IA (Hermes / Ollama)
      </h2>
      <p class="text-slate-300 leading-relaxed text-base">{{ result.summary }}</p>
    </section>

    <!-- Success Highlights & Passed Guardrails -->
    <section class="bg-gradient-to-r from-emerald-950/30 to-slate-900/60 border border-emerald-900/40 rounded-2xl p-8 shadow-lg">
      <h2 class="text-xl font-bold text-emerald-300 flex items-center gap-2 mb-4">
        <span>🌟</span> Pontos Fortes e Guardrails Bem Sucedidos
      </h2>
      <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {% for name, category in result.categories.items() %}
          {% if category.score >= 90 %}
          <div class="bg-slate-950/60 border border-emerald-900/30 rounded-xl p-4">
            <div class="flex items-center justify-between">
              <span class="font-semibold capitalize text-emerald-300">
                {% if name == 'finops' %}💰 FinOps{% elif name == 'resilience' %}⚡ Resiliência{% elif name == 'security' %}🛡️ Segurança{% else %}🏛️ Arquitetura{% endif %}
              </span>
              <span class="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">Aprovado ({{ category.score }})</span>
            </div>
            <p class="text-xs text-slate-300 mt-2">Nenhum desvio crítico encontrado. Padrões de robustez e conformidade atendidos com sucesso.</p>
          </div>
          {% endif %}
        {% endfor %}
      </div>
    </section>

    <!-- Categories Breakdown -->
    <section>
      <h2 class="text-xl font-bold text-slate-200 mb-6 flex items-center gap-2">
        <span>📊</span> Análise Detalhada por Categoria
      </h2>
      <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {% for name, category in result.categories.items() %}
        <div class="bg-slate-900/60 border border-slate-800 rounded-xl p-6 flex flex-col justify-between hover:border-slate-700 transition shadow-md">
          <div>
            <div class="flex items-center justify-between">
              <h3 class="capitalize font-semibold text-slate-200 text-lg flex items-center gap-2">
                {% if name == 'finops' %}💰{% elif name == 'resilience' %}⚡{% elif name == 'security' %}🛡️{% else %}🏛️{% endif %}
                {{ name }}
              </h3>
              <span class="px-2.5 py-0.5 text-xs font-bold rounded-md {% if category.grade == 'A' %}bg-emerald-950 text-emerald-300 border border-emerald-800/50{% elif category.grade == 'B' %}bg-cyan-950 text-cyan-300 border border-cyan-800/50{% else %}bg-amber-950 text-amber-300 border border-amber-800/50{% endif %}">
                Nota {{ category.grade }}
              </span>
            </div>
            <div class="mt-4 flex items-baseline gap-2">
              <span class="text-3xl font-extrabold text-slate-100">{{ category.score }}</span>
              <span class="text-xs text-slate-400">/ 100</span>
            </div>
            <!-- Progress Bar -->
            <div class="w-full bg-slate-800 h-2 rounded-full mt-3 overflow-hidden">
              <div class="h-full rounded-full {% if category.score >= 90 %}bg-emerald-500{% elif category.score >= 75 %}bg-cyan-500{% elif category.score >= 60 %}bg-amber-500{% else %}bg-rose-500{% endif %}" style="width: {{ category.score }}%;"></div>
            </div>
          </div>
          <div class="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
            <span>Achados (Findings):</span>
            <span class="font-semibold text-slate-200">{{ category.finding_count }}</span>
          </div>
        </div>
        {% else %}
        <div class="col-span-4 text-slate-400 text-sm">Nenhuma categoria detalhada disponível.</div>
        {% endfor %}
      </div>
    </section>

    <!-- Findings Section -->
    <section>
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-bold text-slate-200 flex items-center gap-2">
          <span>🔍</span> Achados Validados, Vulnerabilidades e Recomendações ({{ result.findings | length }})
        </h2>
      </div>

      <div class="space-y-4">
        {% for finding in result.findings %}
        <article class="bg-slate-900/60 border {% if finding.severity == 'critical' or finding.severity == 'high' %}border-rose-900/60 bg-rose-950/10{% elif finding.severity == 'medium' %}border-amber-900/60 bg-amber-950/10{% else %}border-slate-800{% endif %} rounded-xl p-6 shadow-md transition hover:border-slate-700">
          <div class="flex flex-wrap items-center justify-between gap-3 mb-3">
            <div class="flex items-center gap-2">
              <span class="px-2.5 py-1 text-xs font-bold uppercase tracking-wider rounded-md 
                {% if finding.severity == 'critical' or finding.severity == 'high' %}bg-rose-950 text-rose-300 border border-rose-800/50
                {% elif finding.severity == 'medium' %}bg-amber-950 text-amber-300 border border-amber-800/50
                {% else %}bg-slate-800 text-cyan-300 border border-slate-700{% endif %}">
                Severidade: {{ finding.severity | replace('critical', 'Crítico') | replace('high', 'Alto') | replace('medium', 'Médio') | replace('low', 'Baixo') }}
              </span>
              <span class="px-2.5 py-1 text-xs font-semibold uppercase tracking-wider bg-slate-800 text-slate-300 rounded-md border border-slate-700">
                Categoria: {{ finding.category }}
              </span>
            </div>
            {% if finding.file %}
            <span class="font-mono text-xs text-cyan-300 bg-slate-950/60 px-3 py-1 rounded-md border border-slate-800">
              📁 {{ finding.file }}{% if finding.line %}:L{{ finding.line }}{% endif %}
            </span>
            {% endif %}
          </div>

          <h3 class="text-lg font-bold text-slate-100 mt-2">{{ finding.title }}</h3>
          <p class="mt-2 text-slate-300 leading-relaxed text-sm">{{ finding.description }}</p>

          {% if finding.recommendation and finding.recommendation != 'None' %}
          <div class="mt-4 pt-4 border-t border-slate-800/60 text-sm bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
            <span class="font-semibold text-cyan-400 block mb-1">💡 Recomendação de Correção e Mitigação:</span>
            <p class="text-slate-300">{{ finding.recommendation }}</p>
          </div>
          {% endif %}
        </article>
        {% else %}
        <div class="bg-slate-900/60 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
          <span class="text-3xl block mb-2">🎉</span>
          Nenhum desvio crítico ou finding bloqueante encontrado neste repositório. Código em conformidade com os guardrails estabelecidos!
        </div>
        {% endfor %}
      </div>
    </section>

    <!-- Important Operational Notes -->
    <section class="bg-amber-950/20 border border-amber-900/40 rounded-2xl p-6 text-sm text-slate-300">
      <h3 class="font-bold text-amber-300 flex items-center gap-2 mb-2">
        <span>⚠️</span> Observações Importantes e Recomendações Operacionais
      </h3>
      <p class="leading-relaxed">
        Esta auditoria foi conduzida estritamente de forma local e reproduzível utilizando o modelo local via Ollama. Recomenda-se revisar periodicamente os limites de contexto das chamadas de LLM, garantir o mascaramento de credenciais em ambientes de agentes autônomos e manter as varreduras de segurança ativas.
      </p>
    </section>

    <!-- Provenance / Metadata Footer -->
    <section class="bg-slate-900/40 border border-slate-800/80 rounded-xl p-6 text-xs text-slate-400 flex flex-col md:flex-row items-center justify-between gap-4">
      <div>
        <span class="font-semibold text-slate-300">Modelo LLM (Ollama):</span> {{ result.provenance.model if result.provenance and result.provenance.model else 'hermes3:8b' }} &nbsp;|&nbsp;
        <span class="font-semibold text-slate-300">GitHub ID:</span> {{ result.provenance.github_id if result.provenance and result.provenance.github_id else 'N/A' }}
      </div>
      <div>
        <span class="font-semibold text-slate-300">Hash SDD das Regras:</span> <code class="text-cyan-300 font-mono">{% if result.provenance and result.provenance.sdd_hashes %}{{ result.provenance.sdd_hashes.rules[:12] }}...{% else %}N/A{% endif %}</code>
      </div>
    </section>
  </main>
</body>
</html>
"""


INDEX_TEMPLATE = """<!doctype html>
<html lang="pt-BR" class="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            slate: {
              950: '#020617',
              900: '#0f172a',
              800: '#1e293b',
              700: '#334155',
            }
          }
        }
      }
    }
  </script>
  <title>Hermes Agentic Auditor · AI Ops Ledger</title>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen antialiased selection:bg-cyan-500 selection:text-slate-950">
  <main class="mx-auto max-w-6xl px-6 py-12 space-y-10">
    <!-- Header Hero -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/40 border border-slate-800 rounded-3xl p-8 shadow-2xl">
      <div>
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950 text-cyan-300 text-xs font-semibold uppercase tracking-wider border border-cyan-800/50 mb-3">
          <span>⚡</span> AI Ops Ledger & Intelligence · 100% Local (Ollama)
        </div>
        <h1 class="text-4xl md:text-5xl font-black tracking-tight">Hermes Agentic Auditor</h1>
        <p class="mt-3 text-slate-300 text-base max-w-2xl leading-relaxed">
          Auditorias estáticas, locais e reproduzíveis de projetos de IA. Garanta robustez, segurança com Trivy, FinOps e resiliência em arquiteturas de agentes.
        </p>
      </div>

      <!-- Quick Metrics Dashboard Widget -->
      <div class="grid grid-cols-2 gap-4 bg-slate-950/70 border border-slate-800/80 rounded-2xl p-5 shadow-inner min-w-[280px]">
        <div class="text-center p-2">
          <div class="text-2xl font-black text-cyan-400">{{ stats.total_repos }}</div>
          <div class="text-xs text-slate-400 uppercase tracking-wider font-semibold mt-1">Repositórios</div>
        </div>
        <div class="text-center p-2 border-l border-slate-800">
          <div class="text-2xl font-black text-emerald-400">{{ stats.avg_score }}</div>
          <div class="text-xs text-slate-400 uppercase tracking-wider font-semibold mt-1">Score Médio</div>
        </div>
        <div class="text-center p-2 border-t border-slate-800 col-span-2">
          <div class="text-lg font-bold text-slate-200">{{ stats.total_findings }} <span class="text-xs font-normal text-slate-400">achados totais registrados</span></div>
        </div>
      </div>
    </div>

    <!-- Search / Filter Bar -->
    <div class="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-md">
      <div class="relative w-full sm:w-96">
        <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">🔍</span>
        <input type="text" id="searchInput" placeholder="Filtrar repositórios por nome..." onkeyup="filterReports()" 
          class="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition">
      </div>
      <div class="text-xs text-slate-400 font-medium">
        Mostrando <span id="visibleCount" class="text-cyan-400 font-bold">{{ reports | length }}</span> de {{ reports | length }} auditorias
      </div>
    </div>

    <!-- Reports Grid / List -->
    <section id="reportsList" class="grid gap-6 md:grid-cols-2">
      {% for report in reports %}
      <a href="reports/{{ report.filename }}" class="report-card group bg-slate-900/60 border border-slate-800 rounded-2xl p-6 hover:border-cyan-500/60 hover:bg-slate-900 transition flex flex-col justify-between shadow-lg relative overflow-hidden" data-repo="{{ report.repository.full_name | lower }}">
        <div class="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition"></div>
        <div>
          <div class="flex items-center justify-between mb-4">
            <span class="px-2.5 py-1 text-xs font-semibold uppercase tracking-wider bg-slate-800 text-slate-300 rounded-lg border border-slate-700">
              Modo: {{ report.repository.selection_mode | replace('explicit', 'Explícito') | replace('discovery', 'Descoberta') }}
            </span>
            <div class="flex items-center gap-2">
              <span class="text-2xl font-black {% if report.audit.score >= 90 %}text-emerald-400{% elif report.audit.score >= 75 %}text-cyan-400{% else %}text-amber-400{% endif %}">
                {{ report.audit.score }}
              </span>
              <span class="px-2.5 py-1 text-xs font-bold rounded-md {% if report.audit.grade == 'A' %}bg-emerald-950 text-emerald-300 border border-emerald-800/50{% elif report.audit.grade == 'B' %}bg-cyan-950 text-cyan-300 border border-cyan-800/50{% else %}bg-amber-950 text-amber-300 border border-amber-800/50{% endif %}">
                Nota {{ report.audit.grade }}
              </span>
            </div>
          </div>

          <h2 class="text-xl font-bold text-slate-100 group-hover:text-cyan-400 transition flex items-center gap-2">
            {{ report.repository.full_name }}
          </h2>

          <p class="mt-3 text-sm text-slate-300 line-clamp-2 leading-relaxed">
            {{ report.summary }}
          </p>

          <!-- Category Score Pills -->
          <div class="mt-6 grid grid-cols-4 gap-2">
            {% for cat_name, cat_data in report.categories.items() %}
            <div class="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2 text-center">
              <div class="text-[10px] uppercase text-slate-400 font-medium truncate">
                {% if cat_name == 'finops' %}💰 FinOps{% elif cat_name == 'resilience' %}⚡ Resiliência{% elif cat_name == 'security' %}🛡️ Seg.{% else %}🏛️ Arq.{% endif %}
              </div>
              <div class="text-sm font-bold text-slate-200 mt-0.5">{{ cat_data.score }}</div>
            </div>
            {% endfor %}
          </div>
        </div>

        <div class="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <span>🔍 {{ report.findings | length }} achados registrados</span>
          <span class="text-cyan-400 font-medium group-hover:translate-x-1 transition inline-flex items-center gap-1">Ver relatório completo →</span>
        </div>
      </a>
      {% else %}
      <div class="col-span-2 bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
        <span class="text-4xl block mb-3">📂</span>
        Ainda não há relatórios publicados.
      </div>
      {% endfor %}
    </section>

    <!-- Footer -->
    <footer class="pt-8 border-t border-slate-800 text-center text-xs text-slate-500">
      Hermes Agentic Auditor · AI Ops Ledger © 2026
    </footer>
  </main>

  <script>
    function filterReports() {
      const input = document.getElementById('searchInput').value.toLowerCase();
      const cards = document.querySelectorAll('.report-card');
      let visible = 0;
      cards.forEach(card => {
        const repo = card.getAttribute('data-repo');
        if (repo.includes(input)) {
          card.style.display = '';
          visible++;
        } else {
          card.style.display = 'none';
        }
      });
      document.getElementById('visibleCount').textContent = visible;
    }
  </script>
</body>
</html>
"""


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

        # Compute stats for index
        total_repos = len(entries)
        avg_score = round(sum(e["audit"]["score"] for e in entries) / total_repos, 1) if total_repos > 0 else 0.0
        total_findings = sum(len(e.get("findings", [])) for e in entries)
        stats = {
            "total_repos": total_repos,
            "avg_score": avg_score,
            "total_findings": total_findings
        }

        path = self.output_dir / "index.html"
        path.write_text(self.environment.from_string(INDEX_TEMPLATE).render(reports=entries, stats=stats), encoding="utf-8")
        return path
