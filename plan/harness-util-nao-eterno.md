# Implementation Plan: Harness útil, não eterno

## Overview

Incorporar no `opencode-config` as regras de harness útil (defeito
real, orçamento finito, catálogo só referência). Destino: o editor
entrevista (5 perguntas), spawna o especialista, mede e só então
grava; o curador continua guardião e valida depois. Sem scripts em
`harness/` deste repo.

Status: em execução.

## Execution Models

- Executor: `gpt-5.6-luna`
- Revisor: `claude-sonnet-4.6`

## Architecture Decisions

- **D1 — Alvo do plano:** incorporar as regras no produto
  `opencode-config` (agentes, `docs/workflow-curadoria.md`,
  skill `harness-catalog`, default-artifacts e testes). Não é
  o harness de um projeto-alvo.
- **D2 — Papéis:** o `curador-produto` continua só guardião:
  valida depois (orçamento, ferramenta morta, cache com
  fallback, finding bloqueante acionável). Não entrevista
  check, não escreve script, não corta check. Achado → pede
  ao humano chamar o editor. O `curador-produto-editor`
  entrevista, propõe orçamento, escolhe ferramentas com o
  humano, implementa, mede e grava `AGENTS.md` +
  `harness/*`. Único que altera esses artefatos.
- **D3 — Implementação dos scripts:** o editor não escreve o
  check sozinho. Spawna o especialista do domínio
  (`eng-software`, `dba`, `sec`, `qa`, `front`, `rev`) com
  contrato (interface JSON, checks aprovados, orçamento,
  bloqueante vs melhoria, proibição de afrouxar gate).
  Editor integra, mede e devolve ao humano. Permissão
  `task`: allow só nesses seis; deny no resto.
- **D4 — Entrevista por check:** antes de criar script, o
  editor pergunta (uma de cada vez) para cada candidato:
  (1) risco que outro check aprovado não pega; (2) está no
  toolchain (wrapper, registry, licença) — se a empresa não
  pode usar ou o bootstrap não instala, não entra no
  caminho feliz; (3) tempo esperado — se não souber, mede
  protótipo antes de gravar no `AGENTS.md`; (4) bloqueante
  ou melhoria — bloqueante exige caminho de resolução;
  timeout de rede não vira pass; (5) se caro e
  determinístico, prever fingerprint SHA-256 + estado em
  `harness/target/` (não versionado) + fallback para a
  suíte completa.
- **D5 — Orçamento de tempo:** tetos sugeridos (humano
  ajusta por projeto): check isolado barato < 15s;
  harness quente (cache hit) < 30s; harness frio
  aceitável < 3 min; soma dos 6 no caminho quente < 10
  min. Estouro só com aprovação explícita e motivo. Se a
  medição estourar: propor fingerprint, retry ou
  retirada — nunca silenciar o check. Humano escolhe.
- **D6 — Contrato do script:** sem argumentos; UTF-8
  forçado em stdout/stderr; eco de progresso em stderr
  (não ecoar a linha JSON do resultado); JSON final = um
  objeto, último bloco com `status` preenchido; exit 0 =
  pass, 1 = fail; retry em falha transitória de rede (até
  3) — esgotou: bloqueante + "chame o humano / resolva a
  rede"; proibido bypass, `failOnViolation=false`, excluir
  teste do scan, fail-open em audit, cache sem fallback;
  ferramenta ausente = finding `melhoria` + instrução de
  instalação, salvo se o humano retirar do escopo.
- **D7 — Catálogo é referência no agente:** a regra vive no
  `curador-produto-editor` (eco na skill e no workflow). O
  catálogo não grava check sozinho. O `AGENTS.md` do
  projeto-alvo só lista o que o humano aprovou na
  entrevista. Humano pode retirar um check — some do
  script e do `AGENTS.md`. Não pular integração/e2e só
  para o harness ficar mais rápido.
- **D8 — Ciclo de medição:** o editor acumula decisões da
  entrevista sem criar arquivo; spawna o especialista de
  cada agente com harness; mede o tempo de parede de cada
  ferramenta; devolve tabela tempo × status ao humano; se
  estourar o orçamento, propõe fingerprint, retry ou
  retirada (humano escolhe); só então grava script +
  tabela no `AGENTS.md` e commita a unidade lógica.
- **D9 — Estático cobre teste:** se o harness tiver análise
  estática, código de teste entra no mesmo scan e no mesmo
  nível de qualidade que produção.

## Task List

Não criar scripts em `harness/` deste repo. O alvo é o
produto (agentes, workflow, skill, template e testes).
Manter os títulos `Fase 3 — Revisão do Harness` e
`Fase 4 — Implementação` — testes atuais dependem deles.
Wrap a 120 colunas. PT-BR com acentuação. Sem `skip` nos
testes. Sem timeout genérico novo.

### Phase 1: Contrato do editor

- [ ] Task 1: Testes do contrato do editor
- [ ] Task 2: Atualizar `curador-produto-editor.md`

### Checkpoint: Editor

- [ ] Testes novos do editor falham no código antigo e
      passam depois da Task 2
- [ ] Testes antigos de fase/proibições continuam verdes
- [ ] Commit local da unidade: testes + editor

### Phase 2: Guardião

- [ ] Task 3: Testes da validação pós-harness do curador
- [ ] Task 4: Atualizar `curador-produto.md`

### Checkpoint: Guardião

- [ ] Curador ainda não edita `AGENTS.md` / `harness/*`
- [ ] Commit local: testes + curador

### Phase 3: Sync e referência

- [ ] Task 5: Sincronizar `docs/workflow-curadoria.md`
- [ ] Task 6: Atualizar skill e `harness-section.md`

### Checkpoint: Complete

- [ ] `.\.venv\Scripts\pytest.exe -m "unit or tools or copilot"`
- [ ] Workflow e editor ainda compartilham os elementos
      já cobertos por `test_editor_and_workflow_contain_same_key_elements`
- [ ] Commit local: workflow + skill + default-artifact

---

## Task 1: Testes do contrato do editor

**Description:** Acrescentar asserts em
`tests/agents/test_curador_produto_editor.py` cobrindo
D3–D9 no texto do editor. TDD: commitar/escrever testes
antes de editar o agente. Não alterar asserts antigos
(Fase 1–4, PROIBIDO criar script antes da Fase 3, etc.).

**Acceptance criteria:**
- [ ] Falham contra o editor atual
- [ ] Cobrem: `task` allow dos 6 especialistas +
      `"*": deny`; entrevista das 5 perguntas; tetos
      15s/30s/3 min/10 min; spawn do especialista;
      contrato D6 (UTF-8, stderr, retry 3, sem bypass);
      ciclo D8 (mede antes de gravar); D9 (estático
      cobre teste); D7 (catálogo é referência)
- [ ] Sem `skip`

**Verification:**
- [ ] `.\.venv\Scripts\pytest.exe tests/agents/test_curador_produto_editor.py -m unit`
      — novos testes FAIL, antigos PASS

**Dependencies:** None

**Files likely touched:**
- `tests/agents/test_curador_produto_editor.py`

**Estimated scope:** Small (1-2 files)

**Commit checkpoint:** juntar com Task 2.

---

## Task 2: Atualizar `curador-produto-editor.md`

**Description:** Gravar D3–D9 no editor. Não mudar Fase 1/2
nem o template do `docs/README.md`.

Passos:
1. Frontmatter `permission.task` — copiar o padrão do
   `curador-produto.md`, mas só estes allows:

```yaml
  task:
    eng-software: allow
    dba: allow
    sec: allow
    qa: allow
    front: allow
    rev: allow
    "*": deny
```

2. Fase 3 — além de linguagem + item a item, exigir as
   5 perguntas (D4) por candidato a check, uma de cada
   vez; catálogo só como referência (D7); acumular sem
   arquivo.
3. Fase 4 — não escrever o check sozinho: spawnar o
   especialista com briefing (JSON, checks aprovados,
   orçamento, bloqueante vs melhoria, D9, proibido
   afrouxar gate). Medir parede, devolver tabela, só
   então gravar script + `AGENTS.md` (D8). Estouro: D5.
4. Seção Interface — acrescentar D6 (UTF-8, eco stderr,
   retry 3, proibições). Manter schema JSON atual
   (`status`, `findings`, `prompt`) para não quebrar
   `test_curador_produto_editor_contains_json_harness_interface`.
5. Limites — editor não corta check sozinho; não copia
   catálogo sem entrevista.

**Acceptance criteria:**
- [ ] Task 1 passa
- [ ] Títulos Fase 3/4 intactos
- [ ] Continua único a alterar `AGENTS.md` e `harness/*`

**Verification:**
- [ ] Mesmo pytest da Task 1 — tudo PASS

**Dependencies:** Task 1

**Files likely touched:**
- `agents/curador-produto-editor.md`

**Estimated scope:** Small (1-2 files)

**Commit checkpoint:** `test(agents): contrato do editor de harness`
(arquivos: as duas da Phase 1). Sem `git push`.

---

## Task 3: Testes da validação pós-harness do curador

**Description:** Asserts em
`tests/agents/test_curador_produto_editor.py` (mesmo
arquivo, funções do `curador-produto`) cobrindo D2: o
guardião valida depois e não edita.

**Acceptance criteria:**
- [ ] Texto do curador cita: orçamento aprovado;
      ferramenta morta (sempre `melhoria` por ausência);
      cache com fallback; finding bloqueante com
      instrução acionável
- [ ] Continua sem validar requisitos e sem "Mapa do
      Produto" (asserts antigos)
- [ ] Continua mandando o humano chamar o editor (não
      edita, não entrevista check)

**Verification:**
- [ ] Novos testes FAIL antes da Task 4

**Dependencies:** Task 2

**Files likely touched:**
- `tests/agents/test_curador_produto_editor.py`

**Estimated scope:** Small (1-2 files)

**Commit checkpoint:** juntar com Task 4.

---

## Task 4: Atualizar `curador-produto.md`

**Description:** Incluir o que o curador verifica depois
(D2), sem virar entrevistador. Manter: não edita
docs/harness; mensagem pré-definida; bash só em
`harness/`, `scripts/` e install de deps.

**Acceptance criteria:**
- [ ] Task 3 passa
- [ ] Não ganha `task` de especialistas para criar
      script (isso é do editor)
- [ ] Achado → pedir ao humano chamar o editor

**Verification:**
- [ ] `.\.venv\Scripts\pytest.exe tests/agents/test_curador_produto_editor.py -m unit`

**Dependencies:** Task 3

**Files likely touched:**
- `agents/curador-produto.md`

**Estimated scope:** Small (1-2 files)

**Commit checkpoint:** `test(agents): validacao pos-harness do curador`

---

## Task 5: Sincronizar `docs/workflow-curadoria.md`

**Description:** Alinhar Fase 3/4 e a interface do
workflow às D3–D8. Agentes não conhecem workflow (nota
P6), mas o doc de design não pode contradizer o editor.
Não reescrever Fase 1/2 nem o mermaid além do
necessário.

**Acceptance criteria:**
- [ ] Fase 3 descreve as 5 perguntas e "acumula sem
      criar arquivo"
- [ ] Fase 4 descreve spawn + medição + tabela + só
      então gravar
- [ ] Interface inclui D6 (UTF-8, stderr, retry, sem
      bypass)
- [ ] Catálogo citado como referência, harness efetivo
      no `AGENTS.md`
- [ ] `test_workflow_describes_standard_json_interface`
      e `test_workflow_does_not_contain_old_harness_interface`
      continuam verdes

**Verification:**
- [ ] `.\.venv\Scripts\pytest.exe tests/scaffold/test_mapa_produto.py -m unit`

**Dependencies:** Task 4

**Files likely touched:**
- `docs/workflow-curadoria.md`

**Estimated scope:** Small (1-2 files)

**Commit checkpoint:** juntar com Task 6.

---

## Task 6: Skill e default-artifact

**Description:** Eco da D7/D6 na skill e no template.
Não copiar Semgrep/ZAP/PSSA como obrigação.

Passos:
1. `skills/harness-catalog/SKILL.md` — a nota já diz
   "não são regras obrigatórias"; trocar o destino
   stale `/doc/README.md` por `AGENTS.md`; acrescentar
   UTF-8, eco stderr, retry 3 e proibições da D6 na
   Interface Padronizada. Não apagar as sugestões por
   agente (continuam catálogo).
2. `agents/default-artifacts/harness-section.md` —
   manter a tabela e `SEM HARNESS A PEDIDO DO HUMANO`.
   Trocar `[a definir com humano]` por ponteiro: critérios,
   orçamento e ferramentas saem da entrevista do editor
   (D4/D5). Mencionar `harness/target/` como estado não
   versionado (fingerprint). Não listar ferramenta nova.

**Acceptance criteria:**
- [ ] Skill não afirma que harness efetivo fica no
      `/doc/README.md`
- [ ] Template não impõe ferramenta de catálogo
- [ ] Scaffold/testes de `harness-section` (agentes na
      tabela, interface JSON, sem harness dos
      não-executores) continuam verdes

**Verification:**
- [ ] `.\.venv\Scripts\pytest.exe tests/scaffold/test_mapa_produto.py tests/agents/test_curador_produto_editor.py -m unit`

**Dependencies:** Task 5

**Files likely touched:**
- `skills/harness-catalog/SKILL.md`
- `agents/default-artifacts/harness-section.md`

**Estimated scope:** Small (1-2 files)

**Commit checkpoint:** `docs(workflow): sync harness util e nao eterno`
(arquivos: Tasks 5–6). Sem `git push`.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mudar título da Fase 3/4 quebra testes | Med | Não renomear as fases |
| YAML `task` inválido derruba o agente | High | Copiar o bloco do `curador-produto.md` |
| Workflow e editor divergem | Med | Task 5 depois do editor; rodar scaffold tests |
| Template copiar catálogo (D7) | Med | Só ponteiro à entrevista; sem ferramenta nova |
| Timeout genérico em texto de script | Med | Não introduzir; estouro vai a fingerprint/retry/retirada |
| Escopo vazar para `harness/` deste repo | Low | Overview: produto só, sem scripts locais |

## Open Questions

Nenhuma — ramos D1–D9 resolvidos.

