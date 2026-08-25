# Implementation Plan: Harness útil, não eterno

## Overview

Incorporar no `opencode-config` as regras de harness útil (defeito
real, orçamento finito, catálogo só referência). Destino: o editor
entrevista (5 perguntas), spawna o especialista, mede e só então
grava; o curador continua guardião e valida depois. Sem scripts em
`harness/` deste repo.

Status: incremento 2 — plano completo, aguardando aprovação.

Incremento 1 (D1–D9, A1) encerrado tecnicamente. Este
incremento altera o resultado: artefatos auto-contidos,
Fase 3 menos tediosa, relatório consolidado.

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
- **D10 — Artefatos auto-contidos:** agentes, workflow,
  skill, template e testes não citam IDs de plano (`D9`,
  `D4`, etc.) nem “ver o plano”. A regra fica escrita por
  extenso no artefato. `plan/harness-util-nao-eterno.md`
  sai no commit final desta unidade.
- **D11 — Fase 3 ajuda a escolher, não interroga em série:**
  aceitou o template padrão → não reperguntar cada
  entrada. Humano oferece ferramenta → editor analisa os
  5 pontos (risco, toolchain, tempo, bloqueante/melhoria,
  fingerprint) e apresenta o parecer. Humano pede
  sugestão → editor mostra as melhores do
  catálogo/toolchain com essas considerações. Depois
  sugere medir os harness escolhidos (tempos reais). Os
  5 pontos continuam; o agente faz o trabalho.
- **D12 — Relatório gerado por coletor:** destino
  `docs/harness.md` (página Markdown versionada;
  `AGENTS.md` só a tabela de comando). O editor não
  inventa métrica na mão. Orienta o humano a criar o
  coletor (script ou equivalente, por stack) que mede e
  gera esse Markdown. Humano aprova o coletor; o arquivo
  sai da execução, não de chute.

## Task List

Não criar scripts em `harness/` deste repo. O alvo é o
produto (agentes, workflow, skill, template e testes).
Manter os títulos `Fase 3 — Revisão do Harness` e
`Fase 4 — Implementação` — testes atuais dependem deles.
Wrap a 120 colunas. PT-BR com acentuação. Sem `skip` nos
testes. Sem timeout genérico novo.

### Phase 1: Contrato do editor

- [x] Task 1: Testes do contrato do editor
- [x] Task 2: Atualizar `curador-produto-editor.md`

### Checkpoint: Editor

- [x] Testes novos do editor falham no código antigo e
      passam depois da Task 2
- [x] Testes antigos de fase/proibições continuam verdes
- [x] Commit local da unidade: testes + editor

### Phase 2: Guardião

- [x] Task 3: Testes da validação pós-harness do curador
- [x] Task 4: Atualizar `curador-produto.md`

### Checkpoint: Guardião

- [x] Curador ainda não edita `AGENTS.md` / `harness/*`
- [x] Commit local: testes + curador

### Phase 3: Sync e referência

- [x] Task 5: Sincronizar `docs/workflow-curadoria.md`
- [x] Task 6: Atualizar skill e `harness-section.md`

### Checkpoint: Complete

- [ ] `.\.venv\Scripts\pytest.exe -m "unit or tools or copilot"`
- [x] Workflow e editor ainda compartilham os elementos
      já cobertos por `test_editor_and_workflow_contain_same_key_elements`
- [x] Commit local: workflow + skill + default-artifact

### Phase 4: Incremento 2 — artefato e Fase 3

- [ ] Task 7: Ajustar testes D10–D12
- [ ] Task 8: Reescrever Fase 3/4 do editor (e eco no curador se
      `docs/harness.md` entrar na validação)

### Checkpoint: Editor incremento 2

- [ ] Sem `D9`/`D4`/`uma de cada vez` nos artefatos produtivos
- [ ] Commit: testes + editor (+ curador se tocado)

### Phase 5: Sync incremento 2

- [ ] Task 9: Workflow + skill + template

### Checkpoint: Incremento 2 completo

- [ ] `.\.venv\Scripts\pytest.exe tests/agents/test_curador_produto_editor.py tests/scaffold/test_mapa_produto.py tests/skills/test_harness_catalog.py -m unit`
- [ ] Commit: workflow + skill + template
- [ ] Plano deste arquivo sai só no commit final da unidade
      lógica **depois** da aprovação do revisor (D10) — o
      executor **não** remove o plano agora

---

## Task 1: Testes do contrato do editor

**Description:** Acrescentar asserts em
`tests/agents/test_curador_produto_editor.py` cobrindo
D3–D9 no texto do editor. TDD: commitar/escrever testes
antes de editar o agente. Não alterar asserts antigos
(Fase 1–4, PROIBIDO criar script antes da Fase 3, etc.).

**Acceptance criteria:**
- [x] Falham contra o editor atual
- [x] Cobrem: `task` allow dos 6 especialistas +
      `"*": deny`; entrevista das 5 perguntas; tetos
      15s/30s/3 min/10 min; spawn do especialista;
      contrato D6 (UTF-8, stderr, retry 3, sem bypass);
      ciclo D8 (mede antes de gravar); D9 (estático
      cobre teste); D7 (catálogo é referência)
- [x] Sem `skip`

**Verification:**
- [x] `.\.venv\Scripts\pytest.exe tests/agents/test_curador_produto_editor.py -m unit`
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
- [x] Task 1 passa
- [x] Títulos Fase 3/4 intactos
- [x] Continua único a alterar `AGENTS.md` e `harness/*`

**Verification:**
- [x] Mesmo pytest da Task 1 — tudo PASS

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
- [x] Texto do curador cita: orçamento aprovado;
      ferramenta morta (sempre `melhoria` por ausência);
      cache com fallback; finding bloqueante com
      instrução acionável
- [x] Continua sem validar requisitos e sem "Mapa do
      Produto" (asserts antigos)
- [x] Continua mandando o humano chamar o editor (não
      edita, não entrevista check)

**Verification:**
- [x] Novos testes FAIL antes da Task 4

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
- [x] Task 3 passa
- [x] Não ganha `task` de especialistas para criar
      script (isso é do editor)
- [x] Achado → pedir ao humano chamar o editor

**Verification:**
- [x] `.\.venv\Scripts\pytest.exe tests/agents/test_curador_produto_editor.py -m unit`

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
- [x] Fase 3 descreve as 5 perguntas e "acumula sem
      criar arquivo"
- [x] Fase 4 descreve spawn + medição + tabela + só
      então gravar
- [x] Interface inclui D6 (UTF-8, stderr, retry, sem
      bypass)
- [x] Catálogo citado como referência, harness efetivo
      no `AGENTS.md`
- [x] `test_workflow_describes_standard_json_interface`
      e `test_workflow_does_not_contain_old_harness_interface`
      continuam verdes

**Verification:**
- [x] `.\.venv\Scripts\pytest.exe tests/scaffold/test_mapa_produto.py -m unit`

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
- [x] Skill não afirma que harness efetivo fica no
      `/doc/README.md`
- [x] Template não impõe ferramenta de catálogo
- [x] Scaffold/testes de `harness-section` (agentes na
      tabela, interface JSON, sem harness dos
      não-executores) continuam verdes

**Verification:**
- [x] `.\.venv\Scripts\pytest.exe tests/scaffold/test_mapa_produto.py tests/agents/test_curador_produto_editor.py -m unit`

**Dependencies:** Task 5

**Files likely touched:**
- `skills/harness-catalog/SKILL.md`
- `agents/default-artifacts/harness-section.md`

**Estimated scope:** Small (1-2 files)

**Commit checkpoint:** `docs(workflow): sync harness util e nao eterno`
(arquivos: Tasks 5–6). Sem `git push`.

---

## Task 7: Ajustar testes D10–D12

**Description:** TDD no mesmo
`tests/agents/test_curador_produto_editor.py`. Não
apagar cobertura dos 5 pontos, tetos, spawn, D6, estático
em teste. Trocar o *como* da Fase 3 e a coleta de métrica.

**Acceptance criteria:**
- [ ] `test_editor_requires_five_questions_per_harness_check`
      deixa de exigir `"uma de cada vez"`. Passa a exigir
      que o editor: (a) se o template foi aceito, não
      reperguntar cada entrada; (b) se o humano oferece
      ferramenta, analisa os 5 pontos e apresenta parecer;
      (c) se pede sugestão, mostra as melhores com essas
      considerações; (d) sugere medir tempos reais
- [ ] Os 5 pontos continuam no texto (risco, toolchain,
      tempo, bloqueante/melhoria, fingerprint)
- [ ] `test_editor_measures_before_recording_harness` deixa
      de exigir `"tabela tempo × status"` inventada na mão.
      Passa a exigir: orientar o humano a criar um coletor
      (script ou equivalente); coletor gera
      `docs/harness.md`; humano aprova o coletor; só então
      grava scripts/`AGENTS.md`
- [ ] Novo teste: editor, curador, workflow e skill **não**
      contêm IDs `D1`–`D12` nem a frase “ver o plano”
- [ ] Sem `skip`

**Verification:**
- [ ] Pytest do arquivo — novos/ajustados FAIL no editor
      atual; asserts intocados PASS

**Dependencies:** None (incremento 2)

**Files likely touched:**
- `tests/agents/test_curador_produto_editor.py`

**Estimated scope:** Small (1-2 files)

**Commit checkpoint:** juntar com Task 8.

---

## Task 8: Reescrever Fase 3/4 no editor

**Description:** Gravar D10–D12 em
`agents/curador-produto-editor.md`. Título
`Fase 3 — Revisão do Harness` permanece (teste regex).
Não mudar Fase 1/2.

Passos:
1. Tirar `(D9)` e qualquer `D[0-9]+` do arquivo. Manter a
   regra de estático cobrir teste, por extenso.
2. Substituir o bloco das 5 perguntas em série pelo fluxo
   D11 (template aceito / oferece ferramenta / pede
   sugestão / medir).
3. Fase 4: spawn do especialista permanece. Medição via
   coletor aprovado que gera `docs/harness.md` (D12), não
   tabela inventada. Estouro de orçamento ainda vai ao
   humano (fingerprint, retry ou retirada).
4. Curador: só mencionar `docs/harness.md` se for o lugar
   da evidência de orçamento; **não** virar entrevistador.

**Acceptance criteria:**
- [ ] Task 7 passa
- [ ] Sem IDs de plano no editor/curador

**Verification:**
- [ ] `.\.venv\Scripts\pytest.exe tests/agents/test_curador_produto_editor.py -m unit`

**Dependencies:** Task 7

**Files likely touched:**
- `agents/curador-produto-editor.md`
- `agents/curador-produto.md` (só se a evidência de
  orçamento passar a citar `docs/harness.md`)

**Estimated scope:** Small (1-2 files)

**Commit checkpoint:** `fix(agents): fase 3 escolhe e relatorio gerado`

---

## Task 9: Workflow, skill e template

**Description:** Eco D11/D12 e D10 (sem IDs de plano).

1. `docs/workflow-curadoria.md` Fase 3/4 iguais ao editor
   (sem 5 perguntas em série; coletor → `docs/harness.md`).
2. `skills/harness-catalog/SKILL.md` — uma frase: relatório
   humano em `docs/harness.md`, gerado por coletor, não
   chute. Sem `/doc/README.md`. Sem `D12`.
3. `agents/default-artifacts/harness-section.md` — ponteiro
   a `docs/harness.md` como página de métricas; sem
   ferramenta nova de catálogo.

**Acceptance criteria:**
- [ ] Workflow não contém `"uma de cada vez"`
- [ ] Contém `docs/harness.md` e “coletor”
- [ ] Nenhum artefato desta task contém `D9`/`D12`
- [ ] Testes de scaffold e skill continuam verdes

**Verification:**
- [ ] `.\.venv\Scripts\pytest.exe tests/scaffold/test_mapa_produto.py tests/skills/test_harness_catalog.py tests/agents/test_curador_produto_editor.py -m unit`

**Dependencies:** Task 8

**Files likely touched:**
- `docs/workflow-curadoria.md`
- `skills/harness-catalog/SKILL.md`
- `agents/default-artifacts/harness-section.md`

**Estimated scope:** Small (1-2 files)

**Commit checkpoint:** `docs(workflow): sync fase 3 e docs/harness.md`
Sem `git push`. Não apagar este plano nesta task.

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
| Executor apaga o plano antes do revisor | Med | Task 9: não remover o plano agora (D10 só no commit final pós-revisor) |
| Teste antigo exige `"uma de cada vez"` | High | Task 7 troca o assert antes do editor |
| Coletor vira script neste repo | Med | Só instrução no editor; script vive no projeto-alvo |

## Open Questions

Nenhuma — ramos D10–D12 resolvidos.

## Achados da revisão

- **A1 (aceito, melhoria):** frontmatter de
  `skills/harness-catalog/SKILL.md` ainda cita
  `/doc/README.md`. Trocar por `AGENTS.md` e cobrir com
  teste. Commit:
  `fix(skill): corrige destino stale no frontmatter harness-catalog`.
