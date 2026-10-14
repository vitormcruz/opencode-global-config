# Plano: Permissões de delegação (tool task) abertas

## Overview

Os agentes globais em `harness-conf/agents/` carregam no frontmatter um bloco
`permission.task` com `"*": deny` seguido de allowlist estática de agentes.
Essa política bloqueia agentes novos criados por projetos consumidores da
config global: qualquer agente fora da lista é negado pela regra estática,
e reiniciar o opencode não resolve porque a lista é texto fixo no markdown.
Este plano troca a política fechada por uma política aberta (`"*": allow`),
ajusta as guardas de teste que sancionavam a política antiga, ajusta o
adapter Copilot que materializa a allowlist no prompt e registra a decisão
em ADR permanente.

Contexto histórico (levantado em 2026-10-14): a política fechada entrou em
`b416dbe`/`9b185cb` (2026-09-26) como hardening contra (1) falha de spawn
de agente `mode: primary` em runtime ("Unknown subagent type") e (2)
permissão ampla considerada inauditável. A resolução foi creditada à
classificação do `rev` em 2026-09-27 (plano arquivado
`plan/insumo-devflow-spawn-dinamico.md`, commit `dc44d79`), não ao `sec`.
O cenário de projetos com agentes próprios não foi considerado na época.

Estado inicial dos blocos `permission.task` (10 arquivos):

- deny puro, sem allows: `dba`, `eng-software`, `front`, `qa`, `rev`, `sec`
- deny + allowlist: `analista` (revisor-historia), `curador-produto`
  (eng-software), `devflow` (7 agentes), `smart-planner` (8 agentes)
- `revisor-historia` não tem bloco `permission.task`

## Architecture Decisions

- **D1 (aprovada pelo humano em 2026-10-14): política de delegação aberta.**
  Agentes podem spawnar qualquer agente. O padrão `"*": deny` + allowlist
  estática em `permission.task` deixa de existir nos agentes do harness-conf.
  Rationale: projetos consumidores podem definir agentes próprios e usá-los
  com o smart-planner e demais orquestradores; a allowlist estática bloqueava
  isso. Registro permanente em ADR nova (`docs/adr/0012-*`), revogando
  explicitamente a política de hardening de 2026-09-26.
- **D2 (aprovada pelo humano em 2026-10-14): escopo total.** A política
  aberta vale para todos os agentes com bloco `permission.task` (10
  arquivos), incluindo workers que hoje têm deny puro (dba, eng-software,
  front, qa, rev, sec) e `revisor-historia` (sem bloco hoje). Rationale do
  humano: política única, sem categorias de agente.
- **D3 (aprovada pelo humano em 2026-10-14): mapa de skills mantido.**
  A política de skills (deny global em `opencode.json` + allow por agente
  no frontmatter, validada por `tests/agents/test_workflow_consistency.py`)
  permanece inalterada. Só a política de delegação (tool `task`) é aberta.
- **D4 (decisão de implementação): materialização explícita.** Todos os
  11 arquivos de agentes ganham bloco `permission.task` com exatamente
  `"*": allow` (10 trocam o bloco atual; `revisor-historia` ganha bloco
  novo). Explícito e uniforme: não depende do default do opencode nem do
  modo de permissão da sessão.
- **D5 (decisão de implementação): guarda anti-regressão.** O teste de
  guardas passa a reprovar qualquer entrada `deny` em `permission.task`
  (wildcard ou nomeada) e aprovar wildcard allow; a checagem de que allows
  nomeados apontam para agente spawnável permanece para entradas
  residuais. Assim a decisão D1 fica protegida no código.

## Task List

### Phase 1: Política aberta e guardas

- [ ] Task 1: Trocar `permission.task` para `"*": allow` nos agentes
  - **Description:** substituir o bloco `permission.task` atual por
    `task:\n    "*": allow` nos 10 agentes que têm bloco (remover denies e
    allowlists nomeadas) e adicionar o bloco a `revisor-historia.md`.
    Nada mais do frontmatter muda (skills, bash, edit etc. permanecem).
  - **Acceptance criteria:**
    - [ ] `grep -A2 "task:" harness-conf/agents/*.md` mostra só
          wildcard allow; nenhum `deny` em `permission.task`
    - [ ] `revisor-historia.md` tem bloco `permission.task` com wildcard
          allow
    - [ ] Nenhuma linha acima de 120 colunas nos arquivos editados
  - **Verification:** `grep -rn '"\*": deny' harness-conf/agents/` vazio;
    `.venv/bin/pytest tests/agents/ -m all`
  - **Dependencies:** None
  - **Files likely touched:** `harness-conf/agents/{analista,curador-produto,dba,devflow,eng-software,front,qa,rev,revisor-historia,sec,smart-planner}.md`
  - **Estimated scope:** S (11 arquivos, mudança mecânica)

- [ ] Task 2: Reescrever a guarda de `test_task_spawnable_modes.py`
  - **Description:** inverter a política do teste: reprovar qualquer
    entrada `deny` em `permission.task` e aprovar wildcard allow
    (anti-regressão da decisão de política aberta); manter a validação de
    que allows nomeados apontam para agente com mode `subagent` ou `all`.
    Atualizar docstrings que justificam a política antiga.
  - **Acceptance criteria:**
    - [ ] Teste reprova agente com `"*": deny` ou deny nomeado em task
    - [ ] Teste aprova `"*": allow`
    - [ ] Allows nomeados ainda validam spawnability do alvo
    - [ ] Docstrings refletem a política aberta e citam a ADR 0012
  - **Verification:** `.venv/bin/pytest tests/agents/test_task_spawnable_modes.py -m all`
  - **Dependencies:** Task 1 (o repo precisa estar conforme a política
    nova para o teste passar)
  - **Files likely touched:** `tests/agents/test_task_spawnable_modes.py`
  - **Estimated scope:** M

### Checkpoint: after Tasks 1-2
- [ ] `.venv/bin/pytest tests/agents/ -m all` passa
- [ ] Commit local: `feat(agents): abre permissoes de delegacao task`

### Phase 2: Adapter Copilot e registro da decisão

- [ ] Task 3: Adapter Copilot sem allowlist restritiva
  - **Description:** o adapter Copilot deriva do frontmatter a instrução
    "use a ferramenta task somente com estes agent_type". Com wildcard
    allow, passar a instruir o uso com qualquer perfil Copilot
    disponibilizado pelo sync (sem lista restritiva); atualizar testes do
    harness. As funções de parsing de `task_rules` que detectam deny
    (linhas ~140-204) precisam cobrir o caso wildcard allow.
  - **Acceptance criteria:**
    - [ ] Prompt gerado para agentes com `"*": allow` não restringe a
          lista de `agent_type`
    - [ ] Testes do adapter em `tests/harnesses/` cobrem o caso wildcard
          allow
    - [ ] `.venv/bin/pytest tests/harnesses/ -m all` passa
  - **Verification:** `.venv/bin/pytest tests/harnesses/ -m all`
  - **Dependencies:** Task 1
  - **Files likely touched:** `src/opencode_config/harnesses/copilot.py`,
    `tests/harnesses/` (teste específico do adapter Copilot)
  - **Estimated scope:** M

- [ ] Task 4: ADR 0012 registrando a decisão
  - **Description:** criar `docs/adr/0012-permissoes-task-abertas.md`
    autocontida: contexto (bloqueio de agentes de projetos consumidores),
    decisão (delegação aberta com `"*": allow`), decisão complementar
    (mapa de skills mantido), revogação explícita do hardening de
    2026-09-26 (`b416dbe`/`9b185cb`) e da guarda anti-wildcard-allow.
    Seguir o formato das ADRs existentes.
  - **Acceptance criteria:**
    - [ ] ADR existe, é autocontida (sem referência a este plano) e segue
          o formato das existentes
    - [ ] Revoga explicitamente a política anterior e registra que o mapa
          de skills foi mantido por decisão separada
  - **Verification:** leitura da ADR contra `docs/adr/0004-*` como
    referência de formato
  - **Dependencies:** None (pode rodar em paralelo com Task 3)
  - **Files likely touched:** `docs/adr/0012-permissoes-task-abertas.md`
  - **Estimated scope:** S

### Checkpoint: after Tasks 3-4
- [ ] `.venv/bin/pytest -m all` (suíte completa do ambiente) passa
- [ ] Commit local: `feat(harnesses): adapter copilot sem allowlist de task` +
  `docs(adr): registra decisao de permissoes task abertas`

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Spawn de agente `mode: primary` falha em runtime ("Unknown subagent type") — comportamento do opencode que motivou a guarda antiga | Médio: erro explícito na sessão do orquestrador | Aceito pela decisão D1; os prompts dos orquestradores já instruem instância nova de executor/revisor; o erro é claro e acionável |
| Regressão futura: alguém reintroduz allowlist estática | Alto: reproduz o bloqueio de agentes de projeto | Guarda anti-regressão na Task 2 + ADR 0012 |
| Adapter Copilot emitir lista restritiva residual | Médio: comportamento divergente entre harnesses | Task 3 com teste dedicado ao caso wildcard allow |
| Teste de consistência (`test_workflow_consistency.py`) validar algo sobre permissions task | Baixo: suíte falha | Verificar na execução; hoje valida só o mapa de skills |

## Open Questions

(nenhuma; ramos resolvidos: política task aberta, escopo total, mapa de
skills mantido)

## Status

- Fase: plano completo, aguardando aprovação do humano.
- Executor sugerido: `eng-software`; revisor sugerido: `rev`.
- Modelos: a definir com o humano na orquestração.
