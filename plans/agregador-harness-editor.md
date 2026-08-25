# Implementation Plan: Agregador de Harness no curador-produto-editor

## Overview

Atualizar o `curador-produto-editor` e os templates para o editor
sempre propor um agregador genérico: script coletor (não agente, não
gate). Ele não reexecuta harness; lê evidências já persistidas e
artefatos de ferramenta; gera relatório humano versionável em
`docs/harness-report/`. Checks não são inventados: entrevista, proposta,
humano aprova. Depois o editor envia o combinado ao `eng-software`.
Esta entrega não implementa o coletor neste repo.

## Architecture Decisions

- D1: Escopo desta entrega = somente editor e templates neste repo
  (`agents/curador-produto-editor.md`,
  `agents/default-artifacts/harness-section.md` e testes do editor).
  Sem implementar o script coletor do opencode-config.
- D2: O agregador (script) copia o que precisar de `harness/target/`
  para `docs/harness-report/<ferramenta>/` e o MD só referencia essas
  cópias (links relativos). Não linka `target/` nem path de build.
  Origem ausente → não copia; o MD declara ausente. Regeneração
  substitui a subpasta (não acumula lixo).
- D3: Agregador é script determinístico (comando sem args; default
  `harness/agregar`), não é agente. `val-harness` permanece agente de
  validação de evidências e não substitui o script.
- D4: O editor entrevista, propõe e grava o combinado. Não implementa
  nem executa o agregador. Após a aprovação, envia o briefing ao
  `eng-software` para implementar o script.
- D5: O MD apresenta o resultado da ferramenta, não só passou/falhou.
  O editor recomenda ao humano priorizar, sempre que possível, dados
  estruturados nativos (JSON/JUnit/etc.) para o script montar tabelas
  no MD — assim não polui o git. HTML (ou outro report não resumível)
  só é copiado para `docs/harness-report/<ferramenta>/` e linkado.
  Sem métrica inventada; ausente = ausente. Pacote extra só se o
  humano pedir.
- D6: Nesta entrega também alinhar o texto-padrão do scaffold
  (`HARNESS_TEMPLATE`) e os testes que ainda citam
  `docs/harness-report.md` solto. Sem implementar o script coletor.
- D7: Atualizar menções ao caminho antigo em `val-harness`,
  `harness-catalog` e workflow de curadoria. Só o destino do
  agregador; sem mudar o papel desses agentes.
- D8: Achado do revisor aceito. Alinhar a narrativa da Fase 4
  em `docs/workflow-curadoria.md` com D4: o editor não executa
  nem implementa o coletor; envia briefing ao `eng-software`.
  Sem mudar o resto do workflow.

## Task List

Não implementar `harness/agregar` neste repo. Não hardcodar
ferramentas de produto (Vitest, JaCoCo, etc.) como checks.
Nomes de ferramenta no texto só como exemplo de subpasta.

### Phase 1: Contrato do destino

- [ ] Task 1: Atualizar template `harness-section.md`
- [ ] Task 2: Alinhar `HARNESS_TEMPLATE` do scaffold

### Checkpoint: Foundation

- [ ] Os dois templates apontam o mesmo destino novo
- [ ] Nenhum deles usa `docs/harness-report.md` como destino

### Phase 2: Editor (entrevista e handoff)

- [ ] Task 3: Fase 3 — entrevista do agregador
- [ ] Task 4: Fase 4 — briefing para `eng-software`

### Checkpoint: Editor

- [ ] Editor não executa nem grava o script do agregador
- [ ] Entrevista não inventa checks

### Phase 3: Menções e testes

- [ ] Task 5: Path em `val-harness` e `harness-catalog`
- [ ] Task 6: Testes do editor e do scaffold

### Checkpoint: Complete

- [ ] Pytest alvo verde no Windows
- [ ] Pronto para revisão humana

---

## Task 1: Atualizar template harness-section.md

**Description:** Trocar o destino do agregador no template
que o editor copia para o `AGENTS.md` do produto. O texto
é genérico: pasta versionável, um MD índice, subpastas por
ferramenta (nome sai da entrevista).

**Acceptance criteria:**
- [ ] Destino da tabela `## Agregador de Harness` =
      `docs/harness-report/harness-report.md`
- [ ] Nota: único MD na raiz de `docs/harness-report/`;
      subpastas `docs/harness-report/<ferramenta>/`
- [ ] Cópia substitui a subpasta; origem ausente → MD diz
      ausente; links só para a cópia (nunca `target/` nem
      path de build)
- [ ] MD resume dados estruturados da ferramenta; não inventa
      métrica
- [ ] Remover `docs/harness-report.md` como destino

**Verification:**
- [ ] Ler o arquivo e conferir a tabela + notas

**Dependencies:** None

**Files likely touched:**
- `agents/default-artifacts/harness-section.md`

**Estimated scope:** Small (1 file)

**Commit checkpoint:** junto com Task 2

---

## Task 2: Alinhar HARNESS_TEMPLATE do scaffold

**Description:** O bootstrap gera `AGENTS.md` com destino
antigo. Alinhar só o contrato do agregador (comando sem
args + destino novo). Não expandir o scaffold para a
entrevista completa do editor.

**Acceptance criteria:**
- [ ] `HARNESS_TEMPLATE` usa
      `docs/harness-report/harness-report.md`
- [ ] Comando default continua `harness/agregar` sem args
- [ ] Não implementa o script coletor

**Verification:**
- [ ] Conferir o bloco `## Agregador de Harness` no template

**Dependencies:** Task 1 (mesmo contrato)

**Files likely touched:**
- `src/opencode_config/cli/scaffold_mapa.py`

**Estimated scope:** Small (1 file)

**Commit checkpoint:** `docs(harness): destino docs/harness-report/`
(Tasks 1–2)

---

## Task 3: Fase 3 — entrevista do agregador

**Description:** Na Fase 3, depois das entradas por agente,
o editor entrevista o agregador. Não inventa checks. Não
cria o script.

**Acceptance criteria:**
- [ ] Confirmar com o humano: agregador = script coletor,
      não gate que reexecuta os harnesses
- [ ] Confirmar pasta padrão (humano pode escolher outra):
      `docs/harness-report/` + MD índice + subpastas
- [ ] Para cada check **já aprovado**: qual artefato a
      ferramenta emite? JSON/JUnit no MD vs HTML copiado?
- [ ] Recomendar dados estruturados nativos → MD (não polui
      git). Pacote/HTML extra só se o humano pedir
- [ ] Proibido inventar check que o humano não aprovou
- [ ] Proibido criar `harness/agregar` nesta fase

**Verification:**
- [ ] Fase 3 no editor contém os passos acima

**Dependencies:** Task 1

**Files likely touched:**
- `agents/curador-produto-editor.md`

**Estimated scope:** Small (1 arquivo, seção Fase 3)

**Commit checkpoint:** junto com Task 4

---

## Task 4: Fase 4 — briefing para eng-software

**Description:** Hoje a Fase 4 manda o editor executar o
coletor e gravar scripts. Trocar: editor envia o combinado
ao `eng-software`. Spawn dos especialistas por agente
(harness individual) permanece.

**Acceptance criteria:**
- [ ] Remover “executa o coletor” / “só então grava” o
      agregador
- [ ] Após a entrevista, briefing ao `eng-software` com:
      comando, destino, mapa check→artefato, regra de cópia,
      proibições (não reexecutar, não linkar build/target)
- [ ] Editor não implementa o coletor
- [ ] Destino canônico no texto =
      `docs/harness-report/harness-report.md`
- [ ] Proibir MD solto na raiz de `docs/` (não precisa
      repetir o path antigo se isso quebrar asserts)

**Verification:**
- [ ] Fase 4 não manda o editor rodar o agregador

**Dependencies:** Task 3

**Files likely touched:**
- `agents/curador-produto-editor.md`

**Estimated scope:** Small (1 arquivo, seção Fase 4)

**Commit checkpoint:** `docs(editor): entrevista e handoff do
agregador` (Tasks 3–4)

---

## Task 5: Path em val-harness e harness-catalog

**Description:** Trocar só o destino. `val-harness` continua
agente: lê `## Agregador de Harness` e executa o **script**
sem args. Não vira o coletor. Workflows não citam o path
(não criar menção nova).

**Acceptance criteria:**
- [ ] `agents/val-harness.md`: efeito esperado =
      `docs/harness-report/harness-report.md`
- [ ] `skills/harness-catalog/SKILL.md`: mesmo destino
- [ ] Papel de `val-harness` inalterado
- [ ] `docs/workflow-curadoria.md` / `docs/workflow-agentes-dev.md`:
      se não houver path, não editar

**Verification:**
- [ ] Busca por `docs/harness-report.md` como destino = 0
      nos arquivos desta task

**Dependencies:** Task 1

**Files likely touched:**
- `agents/val-harness.md`
- `skills/harness-catalog/SKILL.md`

**Estimated scope:** Small (2 files)

**Commit checkpoint:** junto com Task 6

---

## Task 6: Testes do editor e do scaffold

**Description:** Atualizar asserts do path e cobrir as
regras novas do editor (entrevista, recomendação JSON→MD,
cópia HTML, handoff, não reexecutar). Sem `skip`.

**Acceptance criteria:**
- [ ] `test_curador_produto_editor.py` não exige mais
      `docs/harness-report.md` como destino
- [ ] Exige `docs/harness-report/harness-report.md`
- [ ] Cobre: coletor não reexecuta harness; recomenda
      JSON/JUnit no MD; HTML copiado para subpasta; briefing
      `eng-software`; não inventa checks
- [ ] Ajustar asserts velhos (“só então grava”, “script ou
      equivalente”) para o texto novo da Fase 4
- [ ] `test_mapa_produto.py`: scaffold gera o destino novo

**Verification:**
- [ ] Windows:
      `.\.venv\Scripts\pytest.exe tests/agents/test_curador_produto_editor.py tests/scaffold/test_mapa_produto.py -m "unit or tools or copilot"`

**Dependencies:** Tasks 2, 4, 5

**Files likely touched:**
- `tests/agents/test_curador_produto_editor.py`
- `tests/scaffold/test_mapa_produto.py`

**Estimated scope:** Medium (2 files)

**Commit checkpoint:** `test(harness): destino e regras do
agregador` (Tasks 5–6)

---

## Task 7: Narrativa Fase 4 no workflow de curadoria

**Description:** Achado 1 do revisor. Em
`docs/workflow-curadoria.md` (trechos que dizem que o editor
executa o coletor na Fase 4 e só então grava os scripts),
alinhar com D4. Não expandir o resto do workflow.

**Acceptance criteria:**
- [ ] O workflow não afirma que o editor executa o coletor
- [ ] Afirma que o editor envia briefing ao `eng-software`
- [ ] Destino do relatório permanece
      `docs/harness-report/harness-report.md`
- [ ] Sem outras mudanças de papel no workflow

**Verification:**
- [ ] Os dois trechos citados pelo revisor (~256 e ~438)
      estão alinhados ao editor
- [ ] Testes que assertam o texto antigo do workflow, se
      existirem, atualizados; pytest alvo verde

**Dependencies:** Task 4 (texto canônico no editor)

**Files likely touched:**
- `docs/workflow-curadoria.md`
- testes de workflow, se assertarem o trecho

**Estimated scope:** Small (1–2 files)

**Commit checkpoint:** `docs(workflow): Fase 4 handoff do
agregador`

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Asserts buscam o path antigo e quebram se o texto
  citar a proibição | Med | Task 4: proibir “MD solto na raiz de docs/” sem
  repetir o filename antigo |
| Fase 4 ainda spawna especialistas por agente | Low | Não remover esse spawn; só o agregador vai ao
  eng-software |
| Catalog/val-harness ganharem comportamento novo | Low | D7: só path |
| Executor implementar `harness/agregar` | High | Fora de escopo; D1 |

## Open Questions

Nenhuma. D1–D8 registrados. Achado 1 aceito (Task 7).

## Modelos da execução

- Executor: `gpt-5.6-luna`
- Revisor: `claude-sonnet-5`

---

## Revisão Integrativa

### Achados

| # | Tipo | Descrição | Partes envolvidas | Severidade |
|---|------|-----------|-------------------|------------|
| 1 | Inconsistência | `docs/workflow-curadoria.md` ainda descreve, em dois pontos (linhas ~256–257 e ~438–439), que o `curador-produto-editor` "orienta e executa o coletor aprovado na Fase 4" e que "após a aprovação, executa o coletor e revisa o relatório gerado. Só então grava os scripts". Esse texto contradiz diretamente D4 e o texto já corrigido em `agents/curador-produto-editor.md` Fase 4, que agora diz "O editor não implementa nem executa o coletor" e que, após a entrevista, "envia briefing ao `eng-software`". Apenas o destino (`docs/harness-report/harness-report.md`) foi atualizado nesse arquivo; a narrativa de quem executa o coletor não foi realinhada. O próprio executor sinalizou esse ponto na nota de entrega, mas classificou como coberto por D7 ("só destino"); D7, porém, versa sobre o papel de `val-harness`/`harness-catalog`, não sobre a narrativa de Fase 4 do editor em `docs/workflow-curadoria.md` — nenhuma Task do plano cobriu esse trecho. | `docs/workflow-curadoria.md` ↔ `agents/curador-produto-editor.md` | bloqueante |

### Recomendação

- Achado 1: delegar a `eng-software` (ou ao próprio `curador-produto-editor`,
  dono do artefato) o ajuste da narrativa de Fase 4 em
  `docs/workflow-curadoria.md` (linhas ~256–257 e ~438–439) para refletir
  D4: o editor entrevista, não executa nem implementa o coletor, e envia
  briefing ao `eng-software`. Recomenda-se abrir uma Task adicional (fora
  deste plano ou como follow-up) já que D1–D7 não atribuíram esse trecho a
  nenhuma Task existente.

### Verificações realizadas (sem achados)

- Destino `docs/harness-report/harness-report.md` aplicado de forma
  consistente em `agents/default-artifacts/harness-section.md`,
  `src/opencode_config/cli/scaffold_mapa.py`, `agents/curador-produto-editor.md`,
  `agents/val-harness.md`, `skills/harness-catalog/SKILL.md` e nos três
  arquivos de teste tocados. Nenhuma ocorrência de `docs/harness-report.md`
  solto como destino nesses arquivos.
- Nenhum script/agente `harness/agregar` foi implementado neste repo (busca
  por arquivos "*agregador*" não retornou artefato de implementação, apenas
  o próprio plano).
- `agents/curador-produto-editor.md` Fase 3: entrevista não infere/inventa
  checks (texto explícito "Proibido inventar check que o humano não
  aprovou"), recomenda JSON/JUnit para o MD, HTML copiado para subpasta.
  Fase 4: editor não implementa/executa o agregador; envia briefing ao
  `eng-software` com comando, destino, mapa check→artefato, regra de cópia
  e proibições — aderente a D4.
- `agents/val-harness.md`: mudança restrita ao path do efeito esperado;
  papel (só executa o comando registrado, nunca harness por agente, nunca
  spawna) permanece inalterado — aderente a D7.
- Nenhuma ferramenta de produto (ESLint, Vitest, JaCoCo etc.) foi
  introduzida como check hardcoded pelos commits revisados; menções
  pré-existentes a ESLint/ruff/shellcheck em `docs/workflow-curadoria.md`,
  `skills/harness-catalog/SKILL.md` e `src/opencode_config/cli/scaffold_mapa.py`
  já existiam como exemplos genéricos antes deste plano e não foram
  alteradas por ele.
- Testes: `tests/agents/test_curador_produto_editor.py`,
  `tests/scaffold/test_mapa_produto.py` e `tests/skills/test_harness_catalog.py`
  cobrem as novas regras (destino novo, "não implementa nem executa o
  coletor", "envia briefing ao `eng-software`", JSON/JUnit, HTML, subpasta,
  proibição de inventar check, "não reexecutar harnesses"). Nenhum `skip`
  encontrado nesses arquivos.
- Reexecução de
  `.\.venv\Scripts\pytest.exe tests/agents/test_curador_produto_editor.py tests/scaffold/test_mapa_produto.py -m "unit or tools or copilot"`
  confirmou **64 passed** (evidência independente da sessão do executor).

### Veredicto

[ ] Aprovado sem ressalvas
[ ] Aprovado com melhorias opcionais
[x] Bloqueado — resolver achados bloqueantes antes de
    prosseguir

### Evidências (rev)

- [x] Artefato lido: `plans/agregador-harness-editor.md`
- [x] Plano aprovado consultado: sim
- [x] Checklist integrativo: 6 dimensões verificadas (destino, papel do
      agregador/val-harness, entrevista do editor, não implementação,
      ferramentas hardcoded, cobertura de testes)
- [x] Achados encontrados: 1 total, 1 bloqueante
- [x] Harness script: repositório meta (`opencode-config`) sem seção
      `## Harness` no `AGENTS.md` raiz; usado como evidência o comando de
      verificação definido na Task 6 do próprio plano, reexecutado com
      sucesso (64 passed) — ver acima.
