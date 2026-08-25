# Implementation Plan: Relatório e agregador de harness

## Overview

Renomear o relatório gerado pelo coletor e registrar o
agregador como comando do projeto, com um agente dono da
chamada no workflow. Sem IDs de plano nos artefatos.

Status: em execução.

## Execution Models

- Executor: `gpt-5.6-luna`
- Revisor: `claude-sonnet-4.6`

## Architecture Decisions

- **Relatório:** destino `docs/harness-report.md` (sai
  `docs/harness.md`). É o Markdown gerado pelo coletor,
  não o harness por agente.
- **Registro:** no `AGENTS.md` do projeto-alvo, seção
  própria (não linha da tabela por agente). Campos:
  comando (ex. `harness/agregar`) e destino
  `docs/harness-report.md`. O editor cria/mantém o
  comando como faz com os scripts de harness. Sem
  argumentos, como os outros scripts.
- **Quem chama:** `val-harness` no fim de Construção e
  de Revisão da Construção, quando houve modificação.
  Exceção única à regra “nunca executa harness”: roda
  só o agregador registrado, não os harnesses por
  agente. O editor continua rodando o coletor na Fase 4
  da curadoria (primeiro relatório). Sem IDs de plano
  nos artefatos.

## Task List

Não criar o script agregador neste repo. Só contrato
nos agentes, workflow, skill, template e testes. Wrap
120 colunas. PT-BR com acentuação. Sem `skip`. Sem
timeout genérico novo. Sem `git push`.

### Phase 1: Contrato e editor

- [ ] Task 1: Ajustar testes (TDD)
- [ ] Task 2: Editor + `harness-section.md`

### Checkpoint: Editor

- [ ] Nenhum artefato produtivo cita `docs/harness.md`
- [ ] Commit: testes + editor + template

### Phase 2: Caller e sync

- [ ] Task 3: `val-harness` chama o agregador
- [ ] Task 4: Workflow, skill e (se preciso) `devflow`

### Checkpoint: Complete

- [ ] `.\.venv\Scripts\pytest.exe tests/agents/test_curador_produto_editor.py tests/scaffold/test_mapa_produto.py tests/skills/test_harness_catalog.py -m unit`
- [ ] Commit: val-harness + workflow + skill
- [ ] Este plano sai só no commit final **depois** da
      aprovação do revisor — o executor não remove agora

---

## Task 1: Ajustar testes (TDD)

**Description:** Trocar asserts de `docs/harness.md` e
cobrir registro + caller. Preferir o arquivo existente
`tests/agents/test_curador_produto_editor.py`. Se não
houver teste de `val-harness`, criar
`tests/agents/test_val_harness.py` no mesmo estilo.

**Acceptance criteria:**
- [ ] Editor/skill/template/workflow não são exigidos a
      conter `docs/harness.md`
- [ ] Exigem `docs/harness-report.md`
- [ ] Editor registra o agregador no `AGENTS.md` em
      seção própria (comando + destino)
- [ ] `val-harness` executa o comando do agregador no
      fim da fase; continua sem executar harness por
      agente e sem spawnar
- [ ] Sem `skip`

**Verification:**
- [ ] Pytest dos arquivos tocados — novos FAIL no
      código atual

**Dependencies:** None

**Files likely touched:**
- `tests/agents/test_curador_produto_editor.py`
- `tests/agents/test_val_harness.py` (se criar)

**Estimated scope:** Small (1-2 files)

**Commit checkpoint:** juntar com Task 2.

---

## Task 2: Editor e template

**Description:** Trocar `docs/harness.md` →
`docs/harness-report.md`. Fase 4: orientar coletor;
após aprovação, executar; registrar seção própria no
`AGENTS.md` (comando `harness/agregar` ou o nome que o
humano escolher na entrevista; destino
`docs/harness-report.md`). Template
`harness-section.md`: mesma seção, sem ferramenta de
catálogo.

**Acceptance criteria:**
- [ ] Task 1 (parte editor/template) passa
- [ ] Zero ocorrências de `docs/harness.md` nesses
      arquivos

**Verification:**
- [ ] `.\.venv\Scripts\pytest.exe tests/agents/test_curador_produto_editor.py -m unit`

**Dependencies:** Task 1

**Files likely touched:**
- `agents/curador-produto-editor.md`
- `agents/default-artifacts/harness-section.md`

**Estimated scope:** Small (1-2 files)

**Commit checkpoint:** `fix(agents): registra agregador e harness-report`

---

## Task 3: val-harness chama o agregador

**Description:** No passo de validação, ler a seção do
agregador no `AGENTS.md`. Se houver comando, executá-lo
(bash já permitido) **antes** de cruzar evidências.
Atualizar `docs/harness-report.md` é o efeito do
script; o validador não inventa métrica. Se a seção
estiver ausente, LACUNA (não inventar comando).
Ajustar o “nunca executa harness”: exceção só para o
agregador. Continua sem spawn, sem corrigir artefato,
sem rodar `harness/eng-software` etc.

**Acceptance criteria:**
- [ ] Testes da Task 1 sobre val-harness passam
- [ ] Texto ainda diz que não executa harness por
      agente

**Verification:**
- [ ] Pytest de `tests/agents/test_val_harness.py` e/ou
      o arquivo onde os asserts ficaram

**Dependencies:** Task 2

**Files likely touched:**
- `agents/val-harness.md`
- `tests/agents/test_val_harness.py`

**Estimated scope:** Small (1-2 files)

**Commit checkpoint:** juntar com Task 4.

---

## Task 4: Workflow e skill

**Description:** Eco do contrato, sem IDs de plano.

1. `docs/workflow-curadoria.md` — Fase 4 e interface:
   `docs/harness-report.md`; registro no `AGENTS.md`.
2. `docs/workflow-agentes-dev.md` e/ou `agents/devflow.md`
   — quando spawnar `val-harness`, ele também roda o
   agregador. Não transformar o devflow em executor do
   script.
3. `skills/harness-catalog/SKILL.md` — relatório em
   `docs/harness-report.md`; comando no `AGENTS.md`.

**Acceptance criteria:**
- [ ] Nenhuma ocorrência de `docs/harness.md` no repo
      (exceto histórico git)
- [ ] Scaffold/skill tests verdes

**Verification:**
- [ ] `.\.venv\Scripts\pytest.exe tests/agents/test_curador_produto_editor.py tests/scaffold/test_mapa_produto.py tests/skills/test_harness_catalog.py -m unit`

**Dependencies:** Task 3

**Files likely touched:**
- `docs/workflow-curadoria.md`
- `docs/workflow-agentes-dev.md`
- `agents/devflow.md`
- `skills/harness-catalog/SKILL.md`

**Estimated scope:** Small (1-2 files) — se passar de
5 arquivos, ainda é um eco documental; não partir em
dois commits.

**Commit checkpoint:** `docs(workflow): val-harness roda agregador`
Sem `git push`. Não apagar este plano nesta task.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| val-harness passar a rodar harness por agente | High | Exceção explícita: só o comando do agregador |
| Nome `harness/agregar` virar obrigação de path | Low | AGENTS.md registra o comando real; o exemplo é default |
| `docs/harness.md` residual quebra testes | Med | Task 1 troca asserts antes; grep no checkpoint |
| Script agregador criado neste repo | Med | Overview: só contrato |

## Open Questions

Nenhuma — nome, registro e caller resolvidos.
