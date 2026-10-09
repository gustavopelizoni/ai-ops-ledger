# Hermes Agentic Auditor

Auditor local e estático para repositórios públicos de projetos de IA e agentes.
Usa Hermes via Ollama para interpretação limitada de código, mas mantém seleção,
coleta, validação, pontuação e geração de HTML determinísticas.

## Arquitetura

```text
SDD → Repository Selection → Harness → static collector/analyzer
    → category skills → Hermes/Ollama → schema/evidence validator
    → deterministic scoring → static report → GitHub Pages
```

O Hermes não seleciona repositórios, não executa ferramentas e não gera HTML.
Todo conteúdo do repositório auditado é tratado como dado não confiável.

## Instalação

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
ollama pull hermes3:8b
python scripts/setup_ollama.py
```

O nome do modelo pode variar conforme a instalação. Configure-o sem alterar o
código:

```bash
export OLLAMA_HOST=http://localhost:11434
export HERMES_MODEL=hermes3:8b
export GITHUB_TOKEN= # opcional; eleva o rate limit da API pública
export MAX_CONTEXT_CHARS=9000 # seguro para o contexto padrão de 4k tokens
export OLLAMA_NUM_PREDICT=800
```

## Execução

```bash
python main.py --repo microsoft/autogen
python main.py --repos repos.txt
python main.py --search "topic:ai-agent" --limit 5 --sort stars
```

`--repo`, `--repos` e `--search` são mutuamente exclusivos. Os dois primeiros
auditam estritamente os alvos fornecidos. Busca é ativada somente por `--search`.
Use `--dry-run` para validar e imprimir a seleção sem baixar arquivos nem chamar
o modelo.

Os relatórios são gerados em `site/reports/` e o índice em `site/index.html`.
Dados brutos, manifestos e resultados intermediários ficam em `data/` e são
ignorados pelo Git para reduzir risco de publicar código ou segredos coletados.

## SDD

- `specs/audit_rules.yaml`: regras de categoria, pesos e penalidades.
- `specs/audit_scope.yaml`: extensões, diretórios ignorados e limites.
- `specs/audit_workflow.yaml`: estágios controlados pelo harness.
- `specs/llm_analysis_schema.json`: contrato estrito da resposta do modelo.
- `specs/audit_schema.json`: contrato do resultado pontuado.

Regras podem mudar nos arquivos SDD, mas o workflow não executa YAML arbitrário:
o planner valida a sequência conhecida de estágios.

## Segurança e limites

- Nenhum código, dependência, Dockerfile ou comando do alvo é executado.
- Arquivos são baixados em zip, com limites de tamanho, quantidade, compressão,
  caminhos e symlinks.
- O commit auditado é fixado antes do download.
- Trechos são selecionados deterministicamente e valores parecidos com segredos
  são redigidos antes da chamada ao modelo.
- Cada finding precisa citar arquivo e linha presentes no contexto enviado.
- JSON inválido recebe no máximo `MAX_LLM_RETRIES=2` novas tentativas.

## 🏛️ Sala Virtual de Operações (AI Operations Room)

O projeto agora conta com uma sala virtual interativa em tempo real (inspirada no `AiOperationsRoom`) para monitorar o Hermes, as skills especializadas e os scripts Python em atividade.

### Como acessar a Sala Virtual

1. Instale as dependências da API:
   ```bash
   .venv/bin/pip install fastapi uvicorn pydantic
   ```

2. Inicie o servidor da sala:
   ```bash
   .venv/bin/python -m uvicorn backend.api:app --host 127.0.0.1 --port 8765
   ```

3. Abra no navegador:
   **[http://127.0.0.1:8765](http://127.0.0.1:8765)**

Na interface, você pode acompanhar os agentes em tempo real (trabalhando, delegando, aguardando), visualizar o escritório em pixel art, conferir o painel e invocar varreduras diretamente pelo botão de auditoria.

## Testes

```bash
pytest -q
```

Os testes usam mocks/fixtures e não exigem GitHub ou Ollama ativos.

## Publicação

O workflow `.github/workflows/deploy.yml` publica somente `site/` quando houver
alterações na branch `main`. Configure **GitHub Actions** como fonte de Pages no
repositório. Auditorias devem continuar rodando localmente; o workflow não
processa código externo.
