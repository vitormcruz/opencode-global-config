# Plano — Implementação do Agente `eng-software`

Status: AGUARDANDO APROVAÇÃO DO HUMANO

---

## 1. Resumo

Criar `agents/eng-software.md` — executor com modos
`plan · build · val` que:
- Planeja implementação de código (consulta humano)
- Constrói via TDD (testes → código → refatoração)
- Aplica ajustes integrativos vindos de revisão
- Persiste resultado no arquivo de planejamento e
  retorna resumo curto (≤ 5 linhas) ao `orq`

---

## 2. Requisitos extraídos do workflow

### 2.1 Premissas que afetam `eng-software`

| # | Regra | Impacto |
|---|-------|---------|
| P2 | Resultado no arquivo + resumo ≤ 5 linhas | Contrato de retorno ao `orq` |
| P3 | Instância nova a cada fase | Sem acúmulo de contexto entre fases |
| P8 | Pós-aprovação, tudo se baseia no plano | Falhas de teste = bugs, não mudança de escopo |
| P9 | Planeje perguntando, execute com autonomia | Plan: consulta máxima; Build: autonomia máxima |
| P10 | Granularidade sensível ao contexto | Avaliar tamanho do plano vs capacidade |
| P11 | Revisão híbrida (especialistas + integrativa) | Recebe feedback do `rev` e aplica ajustes |
| P17 | Regras de escrita do arquivo | Na construção: só marca checkboxes |
| P27 | Construção em 3 etapas TDD | Testes → Código → Análise de refatoração |
| P28 | Testes e código: executa com autonomia | Sem consulta ao humano nestas etapas |
| P29 | Gate de refatoração | Consulta humano se refatoração afeta plano |

### 2.2 Ações por modo

#### Modo PLAN (spawnado por `orq` na fase PLANEJAMENTO)
1. Lê insumo (requisitos/história) do arquivo de planejamento
2. Analisa codebase atual
3. Consulta humano para alinhar escopo (P9)
4. Avalia granularidade — sugere dividir/agregar se necessário (P10)
5. Elabora plano de codificação com etapas numeradas
6. Persiste plano no arquivo de planejamento
7. Retorna resumo curto ao `orq`

#### Modo BUILD (spawnado por `orq` na fase CONSTRUÇÃO)
1. Lê plano aprovado do arquivo de planejamento
2. Executa TDD em 3 etapas (P27, P28):
   - **Etapa 1 — Testes**: escreve testes que devem falhar
   - **Etapa 2 — Código**: implementa até testes passarem
   - **Etapa 3 — Gate de refatoração** (P29):
     - Nada muda → registra decisão e segue
     - Ajuste mínimo → propõe ao humano, registra no arquivo
     - Mudança significativa → registra pausa, atualiza
       Status para `GATE-REFATORAÇÃO`, retorna ao `orq`
3. Marca etapas como concluídas (checkbox) no arquivo (P17)
4. Retorna resumo curto ao `orq`

#### Modo VAL (spawnado por `orq` para ajustes integrativos)
1. Recebe relatório do `rev` via arquivo de planejamento
2. Aplica ajustes integrativos no código
3. Persiste resultado no arquivo
4. Retorna resumo curto ao `orq`

### 2.3 Harnesses

| Harness | Tipo | Modos | Descrição |
|---------|------|-------|-----------|
| Smoke tests pós-construção | prompt | build | Executa todos os testes ao final; só prossegue se passarem |
| Testes existentes intocáveis | prompt | build | Se teste não previsto falhar, não ajustá-lo; registrar e perguntar ao humano |
| Regressão incremental | prompt | build | Após cada modificação, executar testes existentes do código alterado |
| Análise estática | tool | build · val | Usar ferramentas do projeto (lint, sonar, etc.) antes de declarar etapa concluída |

---

## 3. Análise de `rules/DEVELOPING.MD`

### 3.1 O que preservar (incorporar no agente)

- **TDD cycle** (red-green-refactor) — já previsto no workflow
- **Clean Code** — manter como diretriz de codificação
- **Boas Práticas** (12Factor, Pirâmide de Testes) — manter
- **ADRs** — manter como sugestão quando decisão arquitetural
  for identificada
- **PT-BR para comentários**
- **Não commitar sem validação humana** (embora no novo workflow
  isso seja responsabilidade do `orq`/finalização)

### 3.2 O que evoluir

| Antes (DEVELOPING.MD) | Depois (eng-software) |
|---|---|
| Agente monolítico (planeja, executa, revisa, testa) | Executor focado: plan + build + val |
| Spawna @analista-bd, @analista_cyber diretamente | Não spawna ninguém; `orq` coordena |
| Orquestra a revisão e os testes | Revisão = `rev`/especialistas; Testes = `qa`/`sec` |
| Exige "modo planning" do IDE | Modo controlado pelo frontmatter (`plan`/`build`/`val`) |
| Gate de refatoração informal ("confirme com humano") | Gate formalizado com 3 cenários e registro no arquivo (P29) |
| Propõe commit ao final | Finalização é responsabilidade do `curador-produto` |
| Controla todo o fluxo | Responde ao `orq`; faz apenas sua especialidade |

### 3.3 O que descartar

- Orquestração de fases (agora é do `orq`)
- Spawning de outros agentes
- Fase de Revisão completa (agora é dos revisores)
- Fase de Testes completa (agora é do `qa`/`sec`)
- Proposta de commit
- Controle de modos do IDE (planning/build)
- Sugestão de uso do @analista quando não há insumo
  (agora é validação do `curador-produto`)

### 3.4 Decisão sobre `rules/DEVELOPING.MD` e `rules/fluxo_dev.md`

**Proposta**: remover ambos os arquivos após implementação do
`eng-software`. Justificativa:
- O conteúdo relevante será absorvido pelo agente
- O DEVELOPING.MD codifica um workflow monolítico que conflita
  com o novo workflow multi-agente
- O `fluxo_dev.md` é um diagrama Mermaid do mesmo workflow obsoleto
- Manter ambos causaria ambiguidade sobre qual é a fonte de verdade
- As "Boas Práticas de Codificação" e "ADRs" podem ser extraídos
  para uma skill ou mantidos como seção no corpo do agente

**Alternativa**: se houver receio de perder as boas práticas,
extrair a seção "Boas Práticas de Codificação" + "ADRs" para
um arquivo `rules/coding-standards.md` referenciado pelo agente.
O humano decide.

---

## 4. Artefato: `agents/eng-software.md`

### 4.1 Frontmatter

```yaml
---
description: >
  Engenheiro de Software — planeja implementação, constrói
  via TDD (testes, código, refatoração) e aplica ajustes
  integrativos (PT-BR)
mode: primary
temperature: 0.2
permission:
  edit: allow
  bash: allow
  webfetch: deny
  websearch: deny
  task:
    "*": deny
---
```

**Justificativas:**
- `mode: primary` — precisa interagir com humano no gate de
  refatoração e no planejamento (restrição VS Code)
- `bash: allow` — precisa executar testes, lint, comandos de build
- `task: "*": deny` — não spawna outros agentes; `orq` coordena
- `websearch/webfetch: deny` — foco em código local

### 4.2 Corpo (estrutura planejada)

```
1. Identidade
   - Engenheiro de Software, PT-BR
   - Executor spawnado pelo `orq`
   - Nunca orquestra, nunca spawna outros agentes

2. Modos de operação
   2.1 PLAN — Planejamento de implementação
       - Consulta humano (P9)
       - Granularidade (P10)
       - Entrega: plano no arquivo + resumo curto
   2.2 BUILD — Construção TDD
       - Etapa 1: Testes (autonomia total)
       - Etapa 2: Código (autonomia total)
       - Etapa 3: Gate de refatoração (3 cenários)
       - Entrega: checkboxes marcadas + resumo curto
   2.3 VAL — Ajustes integrativos
       - Recebe feedback do rev
       - Aplica correções
       - Entrega: resultado no arquivo + resumo curto

3. Contrato com `orq`
   - Resultado sempre no arquivo de planejamento
   - Resumo de retorno ≤ 5 linhas
   - Atualiza Status quando aplicável (gate)

4. Harnesses
   - Smoke tests pós-construção
   - Testes existentes intocáveis
   - Regressão incremental
   - Análise estática

5. Boas Práticas
   - Clean Code
   - TDD (red-green-refactor)
   - 12Factor
   - Pirâmide de Testes
   - ADRs (sugerir quando decisão arquitetural)

6. Limites
   - Não orquestra fases
   - Não spawna agentes
   - Não faz revisão de si mesmo
   - Não propõe commit (responsabilidade da finalização)
```

### 4.3 Compatibilidade VS Code

O `vscode-sync.ps1` converte `agents/eng-software.md` →
`eng-software.agent.md` em `%APPDATA%\Code\User\prompts\`:
- Strip-AgentFrontmatter mantém apenas `description`
- Resultado funcional em ambas as plataformas
- Nenhuma alteração necessária no script de sync

---

## 5. Testes

### 5.1 Modificação em `tests/opencode-int-test/agents-test.bats`

Adicionar teste:

```bash
@test "behavioral: GET /agent lista o agente eng-software" {
  run curl -sf "${OPENCODE_BASE_URL}/agent"
  assert_success
  assert_output --partial "eng-software"
}
```

### 5.2 Teste de sync VS Code

Verificar se `vscode-sync.ps1` gera corretamente
`eng-software.agent.md` — já coberto pelo teste genérico
existente (se houver) ou adicionar caso específico em
`tests/scripts/bootstrap_repo/`.

---

## 6. Checklist de implementação

- [ ] Criar `agents/eng-software.md` (frontmatter + corpo)
- [ ] Adicionar teste em `agents-test.bats`
- [ ] Validar sync VS Code (executar `vscode-sync.ps1`)
- [ ] Remover `rules/DEVELOPING.MD` (após aprovação)
- [ ] Remover `rules/fluxo_dev.md` (após aprovação)
- [ ] Executar `make test`

---

## 7. Perguntas para o humano

1. **Boas Práticas**: manter no corpo do agente ou extrair
   para `rules/coding-standards.md` referenciado?
2. **ADRs**: manter instruções de ADR no agente ou em arquivo
   separado?
3. **`rules/`**: confirma remoção de ambos os arquivos
   (`DEVELOPING.MD` + `fluxo_dev.md`)?
4. **Modo `val`**: no workflow, a tabela de especialidades
   não lista validação para eng-software ("—"), mas o cabeçalho
   diz `plan · build · val`. Interpreto `val` como "aplicar
   ajustes integrativos recebidos do `rev`". Correto?
