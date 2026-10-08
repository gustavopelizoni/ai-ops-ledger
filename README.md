# The AI Ops Ledger

Laboratório público para estudar, testar e operar agentes autônomos em cloud e
observabilidade. Cada experimento precisa deixar uma trilha verificável: o
problema, o desenho, a execução, as falhas, as evidências e o custo.

## A proposta

Agentes que alteram infraestrutura não devem ser avaliados apenas por uma demo
que "funcionou uma vez". O Ledger transforma cada estudo em uma prova pequena e
reproduzível de engenharia:

- **SDD:** define contexto, riscos e critérios de sucesso antes do código.
- **Implementação:** registra prompts, ferramentas, permissões e configuração.
- **Harness:** testa comportamento, segurança, recuperação e limites de custo.
- **Evidências:** guarda logs, métricas, traces e resultados negativos.
- **Crônica:** converte o resultado em um estudo técnico que outra pessoa pode
  reproduzir.

O foco inicial é **agentes confiáveis para operações de cloud**, especialmente
observabilidade, resposta a incidentes e automação segura. O projeto não promete
autonomia irrestrita: mostra quando o agente deve agir, pedir aprovação ou parar.

## Para quem

- Engenheiros de plataforma, SREs e DevOps que querem avaliar agentes com rigor.
- Times pequenos que precisam automatizar operações sem aumentar o risco.
- Pessoas estudando IA aplicada que preferem evidência a conteúdo genérico.

## Primeiros experimentos sugeridos

1. Agente que investiga um alerta e produz diagnóstico com links para evidências.
2. Agente que propõe uma mudança de configuração, mas exige aprovação humana.
3. Agente que detecta regressão de custo e abre um plano de correção reversível.

Cada experimento deve responder: **o agente foi útil, seguro, reproduzível e
mais barato ou mais rápido que a alternativa manual?**

## Estrutura

- `experiments/`: estudos versionados, com status e evidências.
- `agents/`: prompts, contratos de ferramentas, permissões e políticas.
- `templates/`: padrões para SDDs, harnesses e crônicas.
- `site/`: publicação pública dos resultados.
- `STRATEGY.md`: posicionamento, modelo de distribuição e ofertas derivadas.

## Status

O repositório está na fase de fundação. A prioridade é publicar três
experimentos pequenos, completos e reproduzíveis antes de expandir a plataforma.

## Como acompanhar

Cada estudo publicado deve conter o link para o código, o resultado do harness,
limitações conhecidas e uma forma de contato ou discussão. Falhas são parte do
registro: um experimento que evita uma automação insegura também é um resultado.

## Publicação no GitHub Pages

O site estático fica em `site/` e é publicado pelo workflow
`.github/workflows/pages.yml`.

1. Envie a branch `develop` para o GitHub.
2. Abra `Settings > Pages` no repositório.
3. Em `Build and deployment > Source`, selecione `GitHub Actions`.
4. Acompanhe `Actions > Deploy site to GitHub Pages`.

O endereço esperado para este repositório é
`https://gustavopelizoni.github.io/ai-ops-ledger/`.

O workflow executa `experiments/001/harness.py` antes do deploy e publica o
resultado do baseline heurístico em `evidence/experiment-001-baseline.json`.
Esse resultado valida o contrato do harness, não a qualidade de um modelo de IA.
Para ativar a publicação,
envie a branch `develop` e selecione `GitHub Actions` como fonte em
`Settings > Pages > Build and deployment`.
