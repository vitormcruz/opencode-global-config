# Implementation Plan: Normalização, testes por especialidade e
instruções

## Overview

Ajustar o workflow de dev para três mudanças coordenadas:

1. O `eng-software` normaliza o código dos especialistas no padrão de
   construção (sem reabrir decisão de domínio) antes de commitar.
2. O harness por agente vira suíte de testes automatizados por
   especialidade, executada pelo `qa` na fase Testes. O `sec` fica com
   testes de segurança manuais previstos no planejamento.
3. Prompts informacionais saem do harness. A curadoria passa a gravar
   instruções específicas por agente em uma seção nova do `AGENTS.md`.

Nada disto está implementado. Este arquivo é o artefato de planejamento.

## Modelos de execução

- Executor: `grok-4.6`
- Revisor: `grok-4.6`

## Architecture Decisions

- D1 (aprovada): o `eng-software` reescreve/ajusta tudo que o
  subagente alterou (código, SQL, UI, configs) antes do commit, sem
  mudar decisão de domínio. Se o padrão exigir reabrir domínio,
  devolve ao especialista.
- D2 (aprovada): na Construção, `dba` e `front` produzem artefatos;
  em seguida o `eng-software` faz TDD do próprio código, normaliza
  o lote alheio e só então commita. Sem passo de normalização entre
  especialistas.
- D3 (aprovada): testes automatizados por especialidade só travam na
  fase Testes, executados pelo `qa`. Construção e Revisão da
  Construção não rodam essas suítes. O TDD/smoke interno do
  `eng-software` permanece.
- D4 (aprovada): especialidades das suítes são quatro — backend,
  dados, segurança, frontend. O agente `qa` executa as quatro na
  fase Testes; não existe suíte "qualidade". Conteúdo do harness
  atual do `qa`: cobertura de testes vai para backend (e para
  frontend se houver suíte de UI); prompt instrucional vai para
  a seção de instruções. Acessibilidade fica na suíte frontend.
  `pa11y` (hoje no front) e `axe-core` (hoje no qa) não são
  descartados neste plano: a entrevista de curadoria decide se
  fica um, o outro ou ambos.
- D5 (aprovada, refinada por D9): o `curador-produto` deixa de
  validar evidências na Construção e na Revisão da Construção.
  Valida no fim da fase Testes a evidência do orquestrador.
- D6 (aprovada): no Planejamento o `sec` continua requisitos de
  segurança e passa a gravar roteiro de testes manuais. Na fase
  Testes o `qa` executa a suíte automática de segurança; o `sec`
  executa só o roteiro manual. Achado bloqueante segue o fluxo
  da fase (corrigir + "re-executar?").
- D7 (aprovada): nova seção `## Instruções por Agente` no
  `AGENTS.md` (subseção por agente). Nova fase da entrevista de
  curadoria, depois das suítes, item a item com aprovação
  humana. Cada agente lê a própria subseção no início de
  qualquer tarefa. O campo `prompt` sai da interface JSON das
  suítes. Sem instrução: `SEM INSTRUÇÕES A PEDIDO DO HUMANO`.
- D8 (aprovada): falha de suíte na fase Testes roteia por
  especialidade — backend → `eng-software`; dados → `dba`;
  segurança automática → `sec`; frontend → `front`. Teste
  manual de segurança → `sec` (D6). Depois da correção, o
  `eng-software` normaliza e commita (D1) antes de re-executar.
- D9 (aprovada): um script orquestrador (`harness/testes`) chama
  as quatro suítes e agrega o relatório no fim. O `qa` executa
  só esse comando. Os scripts de especialidade existem para
  organização e entrevista de ferramentas. A tabela no
  `AGENTS.md` lista especialidades e o comando do orquestrador.
  A curadoria inclui criar/aprovar o orquestrador. D5 passa a
  conferir uma evidência (orquestrador rodou). `harness/agregar`
  deixa de existir como coletor separado.
- D10 (aprovada): o `AGENTS.md` do produto fica enxuto — tabela
  das especialidades + comando `harness/testes`, seção
  `## Instruções por Agente`, e um link para o spec. As
  subseções (ferramentas, critérios, orçamento, "o que deve
  conter") vivem no arquivo de spec. Caminho default:
  `<pasta-de-docs>/harness.md`, com pasta default `docs/`.
  O humano pode definir outra pasta de documentação na
  curadoria; o `AGENTS.md` guarda o link aprovado. Agentes
  resolvem o spec por esse link, nunca por path hardcoded.
  Default-artifacts partem em snippet curto do `AGENTS.md` e
  template do spec (`harness.md`). A curadoria entrevista o
  spec nesse arquivo e só grava tabela/link/instruções no
  `AGENTS.md`.

## Task List

### Phase 1: Contratos e artefatos default

- [ ] Task 1: Reescrever o contrato das suítes e o orquestrador
- [ ] Task 2: Template de instruções por agente
- [ ] Task 3: Testes dos artefatos default e da interface

### Checkpoint: Foundation

- [ ] Testes unitários dos scaffolds/defaults passam
- [ ] Nenhum artefato de produção cita D1–D9

### Phase 2: Agentes executores

- [ ] Task 4: Remover harness de Construção/Revisão e ler instruções
- [ ] Task 5: Normalização e commit no `eng-software`
- [ ] Task 6: Fase Testes no `qa` e no `sec`
- [ ] Task 7: Testes de contrato dos agentes executores

### Checkpoint: Executores

- [ ] `pytest` unitário dos agentes alterados passa

### Phase 3: Orquestração e curadoria

- [ ] Task 8: Fluxo do `devflow`
- [ ] Task 9: Entrevista e validação no `curador-produto`
- [ ] Task 10: Testes de `devflow` e curadoria

### Checkpoint: Workflow

- [ ] Consistência workflow ↔ agentes verde

### Phase 4: Docs e catálogo

- [ ] Task 11: README e catálogo de harness
- [ ] Task 12: Testes de README/scaffold restantes

### Checkpoint: Complete

- [ ] `.\.venv\Scripts\pytest.exe -m "unit or tools or copilot"`
- [ ] Pronto para revisão humana

---

## Task 1: Reescrever o contrato das suítes e o orquestrador

**Description:** Trocar "Harness por Agente" por testes
automatizados por especialidade (backend, dados, segurança,
frontend) mais o comando único `harness/testes`. Tirar `prompt`
do JSON. O orquestrador chama as quatro suítes e agrega o
relatório; fail se qualquer suíte falhar. Spec detalhado vai
para o template `harness.md` na pasta de docs; o snippet do
`AGENTS.md` é só tabela + link (D10).

**Acceptance criteria:**
- [ ] Snippet do `AGENTS.md` lista as 4 especialidades,
      `harness/testes` e um link placeholder para o spec
- [ ] Template `harness.md` tem as subseções de spec
- [ ] Não existe `harness/agregar` nem campo `prompt`
- [ ] Interface JSON permanece `{ status, findings[] }`

**Verification:**
- [ ] Testes da Task 3 cobrem o default e a interface

**Dependencies:** None

**Files likely touched:**
- `agents/default-artifacts/harness-section.md`
- `agents/default-artifacts/` (template `harness.md`)
- `agents/references/interface-harness.md`

**Estimated scope:** S

**Checkpoint de commit:** junto com Task 2 (mesma unidade:
artefatos de contrato).

---

## Task 2: Template de instruções por agente

**Description:** Criar o default da seção `## Instruções por
Agente` (subseção por agente, ou
`SEM INSTRUÇÕES A PEDIDO DO HUMANO`).

**Acceptance criteria:**
- [ ] Template existe e cobre os agentes do workflow de dev
- [ ] Não mistura instrução com comando de suíte

**Verification:**
- [ ] Teste da Task 3 lê o template

**Dependencies:** None

**Files likely touched:**
- `agents/default-artifacts/` (novo arquivo de instruções)

**Estimated scope:** S

**Checkpoint de commit:** com Task 1.

---

## Task 3: Testes dos artefatos default e da interface

**Description:** Atualizar testes de scaffold/editor que ainda
exigem harness por agente, `prompt` ou `harness/agregar`.

**Acceptance criteria:**
- [ ] Testes antigos de interface antiga falham se o default
      regressar
- [ ] Novos asserts cobrem 4 especialidades + orquestrador +
      seção de instruções

**Verification:**
- [ ] `.\.venv\Scripts\pytest.exe tests/scaffold tests/agents/test_curador_produto_editor.py -m "unit or tools or copilot"`

**Dependencies:** Task 1, Task 2

**Files likely touched:**
- `tests/scaffold/test_mapa_produto.py`
- `tests/agents/test_curador_produto_editor.py`

**Estimated scope:** M

---

## Task 4: Remover harness de Construção/Revisão e ler instruções

**Description:** No boilerplate dos executores (`dba`, `front`,
`rev`, `eng-software`, `qa`, `sec`): tirar execução de harness
na Construção/Revisão; ler `## Instruções por Agente` no início
de qualquer tarefa.

**Acceptance criteria:**
- [ ] Nenhum desses agentes manda rodar harness na Construção
      ou Revisão
- [ ] Todos mandam ler a subseção própria de instruções no
      início da tarefa
- [ ] Ninguém manda procurar spec de suíte (ferramentas,
      orçamento, "o que deve conter") no `AGENTS.md`; comando
      está na tabela; spec está no link do `AGENTS.md` (default
      `docs/harness.md`, pasta alterável na curadoria)

**Verification:**
- [ ] Teste de boilerplate (Task 7)

**Dependencies:** Task 2

**Files likely touched:**
- `agents/dba.md`
- `agents/front.md`
- `agents/rev.md`
- `agents/eng-software.md`
- `agents/qa.md`
- `agents/sec.md`
- `tests/agents/test_boilerplate_consistency.py`

**Estimated scope:** M

**Checkpoint de commit:** com Task 7, ou sozinho se o diff
passar de ~300 linhas.

---

## Task 5: Normalização e commit no `eng-software`

**Description:** Expandir a capacidade de revisar/commitar:
depois do TDD próprio, inspecionar o lote de `dba`/`front`
(e correções da fase Testes), aplicar clean-code /
code-simplification / TDD sem mudar decisão de domínio;
se precisar reabrir domínio, devolver ao especialista;
só então commitar.

**Acceptance criteria:**
- [ ] Capacidade descreve normalização do lote alheio após o
      TDD (não entre especialistas)
- [ ] Devolução ao especialista se o padrão exigir domínio
- [ ] Continua committer único

**Verification:**
- [ ] Teste de presença da capacidade (Task 7)

**Dependencies:** Task 4

**Files likely touched:**
- `agents/eng-software.md`
- `tests/agents/` (teste do eng-software, se existir)

**Estimated scope:** S

---

## Task 6: Fase Testes no `qa` e no `sec`

**Description:** `qa` executa só `harness/testes` + manuais do
plano. `sec` no planejamento grava roteiro manual; na fase
Testes executa só esse roteiro. Suíte automática de segurança
não é mais responsabilidade do `sec`.

**Acceptance criteria:**
- [ ] `qa` não chama scripts de especialidade um a um
- [ ] `sec` tem saída de roteiro no planejamento e execução
      manual na fase Testes

**Verification:**
- [ ] Testes da Task 7

**Dependencies:** Task 1, Task 4

**Files likely touched:**
- `agents/qa.md`
- `agents/sec.md`

**Estimated scope:** S

---

## Task 7: Testes de contrato dos agentes executores

**Description:** Atualizar testes que congelam texto de harness,
evidências na Construção e capacidades do `qa`/`sec`/
`eng-software`.

**Acceptance criteria:**
- [ ] Assersões novas cobrem D1, D2, D6, D7, D9 no texto dos
      agentes
- [ ] Assersões da interface antiga de harness nos agentes
      são removidas

**Verification:**
- [ ] `.\.venv\Scripts\pytest.exe tests/agents -m "unit or tools or copilot"`

**Dependencies:** Task 4, Task 5, Task 6

**Files likely touched:**
- `tests/agents/test_boilerplate_consistency.py`
- `tests/agents/test_eng_software.py` (se existir)
- `tests/agents/test_qa.py` / `test_sec.py` (se existirem)

**Estimated scope:** M

**Checkpoint de commit:** fecha Phase 2.

---

## Task 8: Fluxo do `devflow`

**Description:** Construção: `dba` → `front` → `eng-software`
(TDD + normalizar lote + commit). Sem curador nessas fases.
Testes: `qa` (orquestrador + manuais) → `sec` (roteiro
manual) → curador (evidência do orquestrador). Falha de suíte
roteia por especialidade (D8), depois D1, depois
"re-executar?".

**Acceptance criteria:**
- [ ] Tabela da fase 4/5/6 bate com D2, D3, D5, D6, D8, D9
- [ ] Description do `devflow` não cita evidência de harness
      na Construção/Revisão

**Verification:**
- [ ] Task 10

**Dependencies:** Task 5, Task 6

**Files likely touched:**
- `agents/devflow.md`

**Estimated scope:** S

---

## Task 9: Entrevista e validação no `curador-produto`

**Description:** Entrevista: confirmar pasta de documentação
(default `docs/`), gravar spec em `<pasta>/harness.md`
(especialidades + orquestrador), depois instruções por agente
no `AGENTS.md`. Grava no `AGENTS.md` só tabela + link
aprovado + instruções. Validação em lote só no fim da fase
Testes (orquestrador rodou). **Atualizar as instruções de uso
dos defaults** no `curador-produto` (hoje manda ler
`default-artifacts/harness-section.md` e gravar spec no
`AGENTS.md`): passar a ler o snippet curto + o template
`harness.md`, perguntar a pasta de docs, proibir copiar
subseções de spec para o `AGENTS.md`, e corrigir "o harness
efetivo fica no AGENTS.md".

**Acceptance criteria:**
- [ ] Fase de harness por agente some; entram suítes +
      orquestrador + instruções
- [ ] Spec detalhado não é copiado para o `AGENTS.md`; o
      link aponta para a pasta de docs aprovada
- [ ] Texto do curador aponta os dois defaults novos, não
      `harness-section.md` como spec no `AGENTS.md`
- [ ] Validação pós-Construção/Revisão some

**Verification:**
- [ ] Task 10

**Dependencies:** Task 1, Task 2, Task 8

**Files likely touched:**
- `agents/curador-produto.md`
- `agents/curador-produto-editor.md`
- `agents/references/mensagens-curadoria.md`

**Estimated scope:** M

---

## Task 10: Testes de `devflow` e curadoria

**Description:** Atualizar testes de fases, evidências e
entrevista.

**Acceptance criteria:**
- [ ] `test_workflow_consistency` e testes de `devflow`/
      curador passam
- [ ] Não restam asserts de harness na Construção

**Verification:**
- [ ] `.\.venv\Scripts\pytest.exe tests/agents -m "unit or tools or copilot"`

**Dependencies:** Task 8, Task 9

**Files likely touched:**
- `tests/agents/test_devflow.py`
- `tests/agents/test_workflow_consistency.py`
- `tests/agents/test_curador_produto.py` (se existir)
- `tests/agents/test_curador_produto_editor.py`

**Estimated scope:** M

**Checkpoint de commit:** fecha Phase 3.

---

## Task 11: README e catálogo de harness

**Description:** README e `harness-catalog` passam a falar em
testes por especialidade + orquestrador + instruções, sem
harness por agente na Construção.

**Acceptance criteria:**
- [ ] Dependências/docs humanas não citam o fluxo antigo como
      vigente
- [ ] Catálogo continua sugerindo ferramentas por
      especialidade, não por executor

**Verification:**
- [ ] Task 12

**Dependencies:** Task 1, Task 9

**Files likely touched:**
- `README.md`
- `skills/harness-catalog/SKILL.md`

**Estimated scope:** S

---

## Task 12: Testes de README/scaffold restantes

**Description:** Fechar asserts que ainda falhem no texto antigo
(`Harness por Agente`, `prompt`, `val-harness`, agregar).

**Acceptance criteria:**
- [ ] Suíte `unit or tools or copilot` verde
- [ ] Nenhum skip

**Verification:**
- [ ] `.\.venv\Scripts\pytest.exe -m "unit or tools or copilot"`

**Dependencies:** Task 11, Task 10, Task 7, Task 3

**Files likely touched:**
- `tests/scaffold/test_mapa_produto.py`
- `README.md` (só se teste exigir)

**Estimated scope:** S

**Checkpoint de commit:** fecha o plano.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Construção avança sem suíte de especialidade | Med | TDD/smoke do `eng-software` permanece; gate real na fase Testes |
| Normalização de SQL/UI quebra domínio | High | D1: devolver ao especialista; não reabrir domínio sozinho |
| `pa11y` vs `axe-core` indefinido | Low | Entrevista de curadoria; este plano não descarta nenhum |
| Muitos testes acoplados ao texto "harness" | Med | Tasks 3, 7, 10, 12 no início de cada fase |
| Orçamento de tempo do harness antigo | Low | Não inventar timeout novo; reusar tetos só se o humano confirmar |

## Open Questions

Nenhum ramo em aberto. `pa11y` vs `axe-core` vs ambos é
entrevista de curadoria, não deste plano.

## Achados de revisão aceitos

Revisor aprovou com melhorias opcionais. Humano pediu aplicar:

1. Alinhar a tabela-resumo de agentes: curador valida evidência
   no fim da fase Testes, não nas revisões.
2. Diagrama da fase Testes deve mostrar o roteamento de falha
   por especialidade, não só o `eng-software`.
3. Checklists de evidência: tirar "Harness script" da
   Construção/Revisão; no `sec`, listar o roteiro manual em vez
   de SAST/secrets/DAST.

