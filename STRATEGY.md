# Estratégia do The AI Ops Ledger

## Tese

Existe muito conteúdo sobre agentes de IA que demonstra capacidade, mas pouco
que demonstra confiabilidade em tarefas operacionais. O Ledger deve ocupar esse
espaço: estudos curtos, técnicos e auditáveis sobre agentes que observam,
decidem e propõem ações em ambientes de cloud.

## Posicionamento

> Um laboratório público de agentes de operações confiáveis, onde cada estudo
> vira evidência técnica, material educativo e uma oferta de implementação.

O projeto não deve tentar ser mais um framework de agentes. O diferencial é o
método de avaliação e o registro de decisões, falhas, aprovações humanas,
rollback e custo.

## Unidade de valor

O ativo principal é o **experimento verificável**. Um experimento completo deve
produzir:

- um problema real e uma hipótese mensurável;
- um SDD e uma implementação mínima;
- um harness executável;
- evidências antes/depois;
- limites, falhas e custo estimado;
- uma crônica curta para publicação;
- uma próxima decisão: adotar, revisar ou rejeitar.

## Público inicial

Comece com engenheiros de plataforma e SREs de empresas pequenas e médias.
Esse público entende o problema, pode reproduzir os testes e tem uma dor clara:
reduzir tempo de diagnóstico sem conceder acesso perigoso a um agente.

## Distribuição e reconhecimento

Para cada experimento:

1. Publique o repositório e uma crônica em português e, quando possível, um
   resumo em inglês.
2. Mostre um artefato verificável: dashboard, trace, log, teste ou vídeo curto.
3. Compartilhe uma falha ou trade-off, não apenas o resultado positivo.
4. Convide duas pessoas a reproduzir o teste e registre as divergências.
5. Consolide os resultados em uma matriz pública de agentes, riscos e custos.

O objetivo dos primeiros 90 dias não é viralizar. É obter três reproduções
externas, uma colaboração e uma conversa comercial qualificada.

## Caminho de monetização

Não comece cobrando pelo acesso ao diário. Use o conteúdo público para gerar
confiança e venda a aplicação do método:

- **Diagnóstico pago:** avaliação de um caso de uso de agente, seus riscos,
  ferramentas e critérios de aprovação.
- **Sprint de implementação:** construção de um agente limitado, com harness,
  observabilidade e aprovação humana.
- **Workshop interno:** treinamento prático usando um experimento reproduzível.
- **Kit premium posterior:** templates, checklists e harnesses adaptados a uma
  stack específica, somente depois de validar demanda.

Uma chamada simples para o projeto pode ser: “Quer testar um agente de operações
sem colocá-lo direto em produção? Eu desenho o experimento, monto as travas e
entrego as evidências.”

## Roadmap de 90 dias

### Dias 1-30: Prova de método

- Publicar um agente de diagnóstico somente leitura.
- Criar harness com cenários normais, ambíguos e maliciosos.
- Medir precisão do diagnóstico, tempo, custo e uso de ferramentas.
- Publicar uma crônica com pelo menos uma falha real.

### Dias 31-60: Prova de utilidade

- Adicionar agente que propõe uma correção reversível, sem executá-la sozinho.
- Testar aprovação humana, idempotência e rollback.
- Convidar pessoas da comunidade para reproduzir o laboratório.
- Transformar dúvidas recorrentes em checklist público.

### Dias 61-90: Prova de negócio

- Oferecer três diagnósticos piloto com escopo fechado.
- Documentar resultados anonimizados e objeções recebidas.
- Escolher uma oferta principal e um público específico.
- Definir preço com base no esforço e no valor, não no número de prompts.

## Métricas de decisão

- **Técnicas:** taxa de sucesso, falsos positivos, tempo até diagnóstico,
  custo por execução, cobertura de testes e taxa de rollback.
- **Comunidade:** reproduções externas, issues úteis, contribuições e convites.
- **Negócio:** conversas qualificadas, pilotos pagos, conversão e horas gastas
  por entrega.

Se um agente não superar a alternativa manual em segurança, tempo ou custo, o
resultado deve ser publicado como “não adotar”. Essa disciplina é parte do
produto.
