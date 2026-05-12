# Teste Comparativo de Consumo de Contexto — Graphify

## Objetivo

Comparar o consumo de contexto (tokens) e a qualidade de resposta de um
LLM ao processar `docs/workflow-agentes-dev.md`:

- **Cenário A**: contexto bruto (conteúdo do arquivo Markdown diretamente)
- **Cenário B**: contexto processado pelo Graphify (`GRAPH_REPORT.md`)

---

## Pré-requisitos

- Graphify instalado: `bash scripts/graphify/install --yes`
- `docs/workflow-agentes-dev.md` disponível no repo

---

## Preparação (fazer uma vez)

```bash
# No WSL, na raiz do repo:
wsl -- bash -ic "cd /mnt/c/Users/<usr>/Projetos/opencode-config && graphify . --no-viz"
```

Isso gera `graphify-out/GRAPH_REPORT.md` — o contexto comprimido do Cenário B.

---

## Pergunta-padrão de teste

Use **exatamente** a mesma pergunta nos dois cenários:

```
Liste todos os agentes do workflow, suas fases de atuação e os contratos
formais que regem o workflow. Para cada contrato, descreva em uma frase o
que ele define.
```

---

## Cenário A — Sem Graphify (baseline)

**Instruções**:
1. Abra uma nova sessão do assistente (contexto limpo).
2. Forneça o conteúdo bruto de `docs/workflow-agentes-dev.md` como contexto.
3. Faça a pergunta-padrão acima.
4. Registre os resultados na tabela abaixo.

**Como fornecer o contexto** (VS Code Copilot Chat):
- Adicione `docs/workflow-agentes-dev.md` ao contexto via `#file`.

**Como fornecer o contexto** (OpenCode):
- Use `/read docs/workflow-agentes-dev.md` antes de fazer a pergunta.

---

## Cenário B — Com Graphify

**Instruções**:
1. Abra uma nova sessão do assistente (contexto limpo).
2. Forneça `graphify-out/GRAPH_REPORT.md` como contexto (não o arquivo bruto).
3. Faça a pergunta-padrão acima.
4. Registre os resultados na tabela abaixo.

**Como fornecer o contexto** (VS Code Copilot Chat):
- Adicione `graphify-out/GRAPH_REPORT.md` ao contexto via `#file`.

**Como fornecer o contexto** (OpenCode):
- Use `/read graphify-out/GRAPH_REPORT.md` antes de fazer a pergunta.

---

## Registro de Resultados

| Métrica                              | Cenário A (bruto) | Cenário B (Graphify) |
|--------------------------------------|-------------------|----------------------|
| Tokens de entrada (estimado)         |                   |                      |
| Tokens de saída                      |                   |                      |
| Agentes listados corretamente (9/9)  |                   |                      |
| Fases de atuação corretas            |                   |                      |
| Contratos listados corretamente (5)  |                   |                      |
| Qualidade geral (1-5)                |                   |                      |
| Observações                          |                   |                      |

### Critérios de avaliação

- **Agentes listados**: deve listar os 9 agentes (orq, eng-software, front,
  curador-produto, dba, sec, rev, qa, val-harness)
- **Fases de atuação**: deve acertar pelo menos as fases de cada agente
  conforme a tabela de especialidades do documento
- **Contratos**: deve listar os 5 contratos (Mapa do Produto, Harness,
  Arquivo de Planejamento, Verificação de Harness, Elementos de Especificação)
- **Qualidade geral**: 1=resposta errada/incompleta, 5=precisa e completa

---

## Observações

- Execute os cenários em sessões separadas para evitar contaminação de contexto.
- `GRAPH_REPORT.md` é gerado pelo Graphify usando o modelo da sessão do IDE —
  não é necessária nenhuma chave de API adicional.
- Se o grafo ficar desatualizado após mudanças no repo, regenere com:
  `wsl -- bash -ic "cd /mnt/c/Users/<usr>/Projetos/opencode-config && graphify . --no-viz --update"`
