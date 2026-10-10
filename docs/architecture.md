# Arquitetura do Hermes Agentic Auditor & AI Ops Ledger

Este documento descreve a arquitetura geral, o fluxo de execução e os componentes do **Hermes Agentic Auditor**, um sistema autônomo, estático, local e reproduzível para auditoria de projetos de IA, agentes autônomos e skills da plataforma.

---

## 🏗️ Visão Geral da Arquitetura

O sistema foi desenhado com o princípio de **privacidade e independência**, executando todo o raciocínio de IA, análise estática e varredura de vulnerabilidades **100% localmente via Ollama e Trivy**, sem depender de APIs de nuvem para o processamento de código.

### Diagrama de Fluxo Geral (Arquitetura em Camadas - Mermaid)

```mermaid
C4Context
    title Diagrama C4 - Arquitetura de Componentes do Hermes Agentic Auditor

    Person(cliUser, "Engenheiro / Operador", "Executa a CLI para auditar repositórios ou skills")
    
    System_Boundary(hermesSystem, "Hermes Agentic Auditor & AI Ops Ledger") {
        Container(cli, "CLI / main.py", "Python / argparse", "Orquestração de comandos, seleções (--repo, --repos, --search, --skill) e publicação")
        
        Container(collectors, "Coletores & Validadores", "GitHubCollector & SkillCollector", "Validação de metadados, pinning de commits, download seguro de ZIPs e parse de skills")
        
        Container(analyzer, "Code Analyzer & Trivy", "Static Code Analyzer + Trivy Scanner", "Varredura de dependências, segredos expostos, guardrails e redação/mascaramento de dados sensíveis")
        
        Container(auditors, "Skills Especializadas de Auditoria", "FinOps, Resilience, Security, Observability", "Auditorias específicas baseadas no SDD (Structured Domain Definition)")
        
        Container(engine, "Motor Local de LLM & Validação", "OllamaClient + Validator + Scorer", "Chamadas REST locais (hermes3:8b), validação estrita de schema JSON e pontuação determinística (A-F)")
        
        Container(reporter, "Gerador de Relatórios", "ReportGenerator", "Geração de dashboards modernos em HTML estático (Tailwind CSS) em PT-BR e relatórios JSON")
    }

    System_Ext(github, "GitHub API / GitHub ZIPs", "Repositórios públicos de código-fonte")
    System_Ext(ollama, "Ollama Local", "Servidor LLM local (http://localhost:11434)")
    System_Ext(trivyBin, "Trivy Binário", "Varredura estática de segurança de infra e código")

    Rel(cliUser, cli, "Executa comando CLI")
    Rel(cli, collectors, "Aciona coleta de alvos")
    Rel(collectors, github, "Baixa zip / valida metadados")
    Rel(collectors, analyzer, "Envia arquivos do repositório/skill")
    Rel(analyzer, trivyBin, "Executa varredura de segurança")
    Rel(analyzer, auditors, "Passa contexto enriquecido e filtrado")
    Rel(auditors, engine, "Envia prompts e recebe análises estruturadas")
    Rel(engine, ollama, "Processa inferência local (temp=0)")
    Rel(engine, reporter, "Alimenta validador e scorer determinístico")
    Rel(reporter, cli, "Salva arquivos no diretório de saída (site/) e data/manifests/")
```

---

## 🔄 Fluxo Detalhado de Execução (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor User as Usuário (CLI)
    participant Main as main.py / HermesAuditor
    participant Collector as GitHub / Skill Collector
    participant Analyzer as CodeAnalyzer & Trivy
    participant Auditor as Auditors (FinOps, Resilience...)
    participant Ollama as Ollama Local (hermes3:8b)
    participant Scorer as Validator & Scorer
    participant Report as ReportGenerator

    User->>Main: Executa `python main.py --repo owner/repo`
    Main->>Collector: Valida e baixa repositório alvo (ZIP seguro)
    Collector-->>Main: Alvo baixado e estruturado
    Main->>Analyzer: Inicia seleção de arquivos e Redaction
    Analyzer->>Analyzer: Executa Trivy Scanner (Segredos & Vulns)
    Analyzer-->>Main: Contexto de código enriquecido
    
    loop Para cada Skill de Auditoria
        Main->>Auditor: Executa auditoria especializada
        Auditor->>Ollama: Envia prompt restrito (POST /api/chat)
        Ollama-->>Auditor: Retorna JSON bruto
        Auditor->>Scorer: Valida Schema e calcula pontuação ponderada
        Scorer-->>Main: Resultado validado e pontuado
    end

    Main->>Report: Compila relatórios consolidados
    Report-->>User: Gera Dashboard HTML (Tailwind) e JSON em site/
```

---

## 🧩 Componentes do Sistema (`agent/` & `skills/`)

### 1. Camada de Entrada e Orquestração
- **`main.py`**: Ponto de entrada da CLI. Aceita argumentos como `--repo`, `--repos`, `--search`, `--skill`, `--dry-run` e gerencia o pipeline de execução.
- **`agent/agent.py` (`HermesAuditor`)**: Orquestrador central que comanda o ciclo de vida completo da auditoria (coleta, análise, auditoria por skills, validação, pontuação e publicação).
- **`agent/config.py`**: Gerenciamento robusto de configurações por variáveis de ambiente (`OLLAMA_HOST`, `OLLAMA_MODEL`, timeouts, limites).

### 2. Coletores e Analisadores
- **`skills/github_collector.py`**: Valida repositórios públicos, resolve commits (*pinning*) e baixa arquivos compactados ZIP de forma segura (respeitando limites de tamanho e proporção de compressão).
- **`skills/skill_collector.py`**: Suporte a importação e validação de skills da plataforma Skills.sh.
- **`skills/code_analyzer.py`**: Seleciona arquivos relevantes, aplica regras de exclusão e redatora/mascara segredos (*redaction*) para proteger dados sensíveis.
- **`agent/trivy.py`**: Integração nativa com o scanner **Trivy** para varredura de vulnerabilidades de dependências, segredos expostos (SEC-002) e desvios de configuração (*misconfigurations*).

### 3. Skills Especializadas e Cliente Ollama
- **`agent/ollama_client.py`**: Cliente REST robusto que interage com a API `/api/chat` do Ollama local (`http://localhost:11434`), garantindo modo determinístico (`temperature: 0`).
- **`skills/*_auditor.py`**: Especialistas por domínio:
  - **FinOps**: Tamanho de prompts, contexto e caching de chamadas de LLM.
  - **Resiliência**: Limites de retentativas, loops, timeouts e circuit breaking.
  - **Segurança**: Proteção contra conteúdo não confiável e achados do Trivy.
  - **Arquitetura / Observabilidade**: Fronteiras de erro, responsabilidades e logs/métricas.

### 4. Validação, Scoring e Publicação
- **`agent/validator.py`**: Validação estrita baseada nos schemas JSON definidos em `specs/`.
- **`agent/scorer.py`**: Motor de pontuação determinística que converte achados em notas (`A`, `B`, `C`, `D`, `F`) com base em pesos ponderados.
- **`skills/report_generator.py`**: Gera páginas HTML estáticas e modernas com Tailwind CSS em **100% Português do Brasil**, incorporando ícones, cartões de pontos fortes, avisos operacionais e o catálogo `reports.json`.

