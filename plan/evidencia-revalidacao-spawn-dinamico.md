# Evidência de revalidação: plugin opencode-task-model@1.3.1 e leva de consistência

Data da execução: 2026-09-27 (fuso -03:00). Executor: eng-software, foreground.
Natureza: baseline de verificação, sem correção. A execução não alterou nenhum
arquivo do repo; o único arquivo escrito é esta evidência. Nenhum commit foi
criado.
Premissa ambiental: JAVA_HOME=/home/vitor/.local/share/jdk (ratificada; o
bootstrap instala e persiste a variável).
Ambiente: WSL/Linux, Python 3.12.3, pytest 9.1.1, pluggy 1.6.0, rootdir
/mnt/e/Projetos/opencode-global-config, configfile pyproject.toml.

## Correções da leva e suíte final (2026-09-28)

Executor: eng-software, foreground. Natureza: correções dos achados do rev
(2026-09-27), suíte final e commit. Premissa ambiental ratificada:
JAVA_HOME=/home/vitor/.local/share/jdk.

### Correções aplicadas

- `harness-conf/AGENTS.base.md`: bullet de `background: true` reescrito com
  a caracterização precisa (sandbox deny-all exceto `read`/`glob`/`grep`/
  `webfetch`; sem `bash` e sem `edit`; execução ou edição em foreground),
  sem citar `worktree` (achados 1 e 7).
- `tests/integration/test_task_model_spawn.py`: watchdog endurecido com
  thread de leitura dedicada + fila com timeout; os limites idle 300 s e
  total 900 s disparam com processo vivo e silencioso (achado 2). Teste
  novo `test_watchdog_mata_processo_silencioso` reproduziu o defeito antes
  do fix (RED: 15 s pendurado sem falha; GREEN: 1.4 s com kill).
- `harness-conf/plugins/opencode-quota/UPSTREAM.md` (novo): ratificação do
  `@slkiser/opencode-quota` sem pin, `versao_ratificada: 4.10.6` via
  `npm view` (2026-09-28). `tests/test_opencode_plugins.py`: teste
  integration de aviso de flutuação (igual passa limpo; diferente emite
  warning com instrução de perguntar ao humano; npm ausente ou erro:
  pytest.fail acionável) + 2 testes unit do mecanismo de warning
  (pendência 7, decisão humana).
- Exclusão dos agentes `worker` e `revisor` (decisão humana, pendência 8):
  `git rm` dos dois arquivos; `smart-planner.md` sem `worker: allow` e
  `revisor: allow` (revisor-historia mantido); `opencode.json` sem o bloco
  `agent`; `copilot.py` sem os dois nomes em `_OPENCODE_ONLY_AGENTS` e
  `_HISTORICALLY_SYNCED_AGENTS`; testes ajustados (`test_opencode.py`,
  `test_copilot.py`, `test_repo_structure.py`,
  `test_task_spawnable_modes.py` com mínimo 12 e 17 alvos observados,
  `test_smart_planner.py`). Grep final sem referência órfã funcional
  (restam papel genérico e guards da exclusão).
- `src/test/groovy/Adr0010Fixture.groovy` (novo) + registro em
  `build.gradle` (backend): a primeira suíte final acusou o fixture
  declarado pelo ADR-0010 sem implementação. Fixture validado com
  `gradle test --tests Adr0010Fixture --no-daemon` (veredito pass no
  estado instalado).

### Suíte completa final

Comando executado:

```
JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m all
```

Counts: 935 passed, 0 failed, 0 error, 0 skipped, 31 deselected. Coleção:
966 itens; os 31 deselecionados são `agent_eval`. Duração: 197.37 s.
Delta da baseline (930): +4 testes novos (watchdog; 2 unit e 1 integration
do quota), +2 casos parametrizados do ADR-0010, -1 teste removido
(test_agents_documents_worker_model_mechanism, seção Worker saiu do
AGENTS.md). Skips: nenhum.

Veredicto: OK (verde total após as correções da leva).

### Testes de consistência finais

Comando executado:

```
JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest \
  tests/agents/test_workflow_consistency.py \
  tests/agents/test_task_spawnable_modes.py -v
```

Counts: 26 passed, 0 failed, 0 skipped (22 + 4). Duração: 2.13 s. Nada
órfão: permissões `task` apontam para agentes existentes e spawnáveis
(17 alvos, worker e revisor fora da lista do smart-planner).

### Evidências (eng-software) — leva de correções 2026-09-28

- [x] Teste novo do watchdog: falhou antes do fix (RED confirmado, 15 s
      pendurado sem falha) e passa depois (1.4 s, kill no idle).
- [x] Testes novos do quota: 2 unit + 1 integration (npm view 4.10.6 =
      versao_ratificada; passou limpo sem warning).
- [x] Suíte completa `-m all` sem seleção reduzida: 935 passed, 0 failed,
      0 skipped, 31 deselected, 197.37 s.
- [x] Consistência: 26/26 passed.
- [x] Grep final worker/revisor: só papel genérico e guards da exclusão.
- [x] Fixture Adr0010Fixture executado no Gradle: pass.

## Baseline pós-ciclo vizinho (2026-09-28)

Data da execução: 2026-09-28 (fuso -03:00). Executor: eng-software, foreground.
Natureza: baseline de verificação, sem correção. Nenhum commit criado.
Estado: HEAD 5d13e6a; o ciclo vizinho (otimização de custo/contexto) aplicou
74 commits e resolveu a colisão de coleção registrada na baseline de
2026-09-27: `tests/skills_mgmt` foi commitado e `test_detect` renomeado para
`test_upstream_detect`. Coleção atual: 961 testes.
Premissa ambiental ratificada: JAVA_HOME=/home/vitor/.local/share/jdk.

### Suíte completa

Comando executado:

```
JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m all
```

Counts: 930 passed, 0 failed, 0 error, 0 skipped, 31 deselected. Coleção:
961 itens, 930 selecionados (`-m all` é atalho traduzido pelo conftest para
`unit or integration`; os 31 deselecionados são `agent_eval`). Duração:
228.26 s (0:03:48). Skips: nenhum. Sem trecho de falha a registrar: a suíte
não teve falha nem erro.

Veredicto: OK (verde total no estado pós-ciclo vizinho). A falha de coleção
da baseline anterior não se repete.

### Testes de consistência

Comando executado:

```
JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest \
  tests/agents/test_workflow_consistency.py \
  tests/agents/test_task_spawnable_modes.py -v
```

Counts: 26 passed, 0 failed, 0 skipped. Duração: 2.12 s.

Por arquivo:

- `tests/agents/test_workflow_consistency.py`: 22 passed.
- `tests/agents/test_task_spawnable_modes.py`: 4 passed.

Por teste (todos PASSED):

`tests/agents/test_workflow_consistency.py`

- test_task_permissions_point_to_existing_agents
- test_extract_task_allow_agents_detects_synthetic_orphan
- test_task_wildcard_deny_must_precede_allows
- test_task_wildcard_deny_order_detects_synthetic_offender
- test_question_orchestration_agents_allow_question_tool
- test_question_permission_parser_detects_synthetic_missing
- test_skill_tables_reference_existing_skills
- test_workflow_agent_references_exist
- test_workflow_skill_references_exist
- test_agent_backtick_skill_references_exist
- test_removed_agents_not_referenced
- test_denied_skills_have_at_least_one_allow
- test_denied_skill_without_allow_is_detected
- test_skill_allows_reference_existing_skills
- test_allow_to_missing_skill_is_detected
- test_domain_skills_have_global_deny
- test_domain_skill_without_global_deny_is_detected
- test_opencode_agent_references_exist
- test_opencode_agent_ghost_reference_is_detected
- test_approved_agents_base_sections_keep_their_anchors
- test_extract_skill_permission_entries_parses_quoted_wildcard
- test_work_records_require_executor_and_model

`tests/agents/test_task_spawnable_modes.py`

- test_task_allow_targets_are_spawnable
- test_task_allow_target_with_primary_mode_is_detected
- test_task_wildcard_allow_is_forbidden
- test_task_wildcard_allow_is_detected

Veredicto: OK (26/26 passed). Desde a baseline de 2026-09-27 o arquivo de
consistência ganhou 2 testes (test_approved_agents_base_sections_keep_their_anchors
e test_work_records_require_executor_and_model), ambos verdes.

### Evidências (eng-software) — baseline 2026-09-28

- [x] Suíte completa `-m all` executada sem seleção reduzida: 930 passed,
      0 failed, 0 error, 0 skipped, 31 deselected, 228.26 s.
- [x] Testes de consistência: 26/26 passed, 0 failed, 0 skipped.
- [x] Nenhum arquivo alterado fora desta evidência; nenhum commit criado.

As seções abaixo são histórico da execução de 2026-09-27, mantidas sem
alteração.

## Resumo executivo

- Suíte completa (`-m all`): FALHA na coleção (1 error, 0 testes executados).
  Causa: arquivo untracked de outra leva colide com teste existente.
- Testes de consistência: 24 passed, 0 failed, 0 skipped.
- Commits do plugin (0f1ce5e, cdde56f, 1041452): nenhum arquivo em src/ ou
  adapters/; verificação confirmada.
- Commit 94d33f6: altera src/opencode_config/harnesses/copilot.py; verificação
  confirmada.

## Item 1: suíte completa

Comando executado:

```
JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m all
```

Resultado: a coleção abortou antes da execução dos testes.

Counts: 887 collected, 1 error (coleção), 31 deselected, 856 selected,
0 passed, 0 failed, 0 skipped, 0 testes executados. Duração: 6.28 s.

Trecho relevante do output:

```
collected 887 items / 1 error / 31 deselected / 856 selected

==================================== ERRORS ====================================
______________ ERROR collecting tests/skills_mgmt/test_detect.py _______________
import file mismatch:
imported module 'test_detect' has this __file__ attribute:
  /mnt/e/Projetos/opencode-global-config/tests/bootstrap/test_detect.py
which is not the same as the test file we want to collect:
  /mnt/e/Projetos/opencode-global-config/tests/skills_mgmt/test_detect.py
HINT: remove __pycache__ / .pyc files and/or use a unique basename for your test file modules
=========================== short test summary info ============================
ERROR tests/skills_mgmt/test_detect.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
======================= 31 deselected, 1 error in 6.28s ========================
```

Diagnóstico (leitura only, sem correção):

- `tests/skills_mgmt/test_detect.py` é untracked: o `git status --short`
  lista `?? tests/skills_mgmt/test_detect.py`, e o comando
  `git log --oneline -- tests/skills_mgmt/test_detect.py` não retorna commit;
  o arquivo nunca foi commitado.
- `tests/bootstrap/test_detect.py` é rastreado e pré-existente.
- A árvore `tests/` não usa `__init__.py` (a listagem de `tests/bootstrap/` e
  de `tests/skills_mgmt/` não mostra o arquivo). O pytest usa importmode
  prepend (default; o pyproject.toml não define importmode) e importa cada
  teste pelo basename; dois arquivos com o stem `test_detect` colidem no
  sys.modules e a coleção aborta.
- O run de referência do insumo (840 passed, 31 deselected, 2026-09-26) é
  anterior ao arquivo untracked. A suíte completa não roda no estado atual do
  worktree por causa de trabalho alheio em andamento (ver seção "Estado do
  worktree"), não por causa do plugin nem da leva de consistência.
- A execução manteve a suíte completa, sem seleção reduzida: nenhum filtro,
  `--ignore` ou remoção de arquivo foi aplicado.

Veredicto: FALHA (erro de coleção; 0 testes executados). A baseline não
reproduz o verde do run de referência (840 passed) neste estado do worktree.
A causa é externa ao escopo revalidado.

## Item 2: testes de consistência

Comando executado:

```
JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest \
  tests/agents/test_workflow_consistency.py \
  tests/agents/test_task_spawnable_modes.py -v
```

Resultado: 24 passed, 0 failed, 0 skipped, 0 deselected. Duração: 2.17 s.

Por arquivo:

- `tests/agents/test_workflow_consistency.py`: 20 passed.
- `tests/agents/test_task_spawnable_modes.py`: 4 passed.

Por teste (todos PASSED):

`tests/agents/test_workflow_consistency.py`

- test_task_permissions_point_to_existing_agents
- test_extract_task_allow_agents_detects_synthetic_orphan
- test_task_wildcard_deny_must_precede_allows
- test_task_wildcard_deny_order_detects_synthetic_offender
- test_question_orchestration_agents_allow_question_tool
- test_question_permission_parser_detects_synthetic_missing
- test_skill_tables_reference_existing_skills
- test_workflow_agent_references_exist
- test_workflow_skill_references_exist
- test_agent_backtick_skill_references_exist
- test_removed_agents_not_referenced
- test_denied_skills_have_at_least_one_allow
- test_denied_skill_without_allow_is_detected
- test_skill_allows_reference_existing_skills
- test_allow_to_missing_skill_is_detected
- test_domain_skills_have_global_deny
- test_domain_skill_without_global_deny_is_detected
- test_opencode_agent_references_exist
- test_opencode_agent_ghost_reference_is_detected
- test_extract_skill_permission_entries_parses_quoted_wildcard

`tests/agents/test_task_spawnable_modes.py`

- test_task_allow_targets_are_spawnable
- test_task_allow_target_with_primary_mode_is_detected
- test_task_wildcard_allow_is_forbidden
- test_task_wildcard_allow_is_detected

Veredicto: OK (24/24 passed). Nada órfão: as permissões `task` apontam para
agentes existentes, a ordem `"*": deny` antes dos allows nomeados está
respeitada, nenhuma permissão nomeada aponta para agente não spawnável e o
wildcard allow é proibido.

## Item 3: git show --stat por commit

Comando executado (um por commit): `git show --stat <commit>`.

### 0f1ce5e: docs(plugin): registra revisao de seguranca do opencode-task-model

```
 .../plugins/opencode-task-model/UPSTREAM.md        | 92 ++++++++++++++++++++++
 1 file changed, 92 insertions(+)
```

Arquivos tocados: `harness-conf/plugins/opencode-task-model/UPSTREAM.md`.
Veredicto: OK (nenhum arquivo em src/ ou adapters/ aparece no commit).

### cdde56f: feat(harness): adiciona plugin provisorio opencode-task-model

```
 README.md                      |  12 ++++
 harness-conf/AGENTS.base.md    |  11 ++++
 harness-conf/opencode.json     |   3 +-
 tests/test_opencode_plugins.py | 129 +++++++++++++++++++++++++++++++++++++++++
 4 files changed, 154 insertions(+), 1 deletion(-)
```

Arquivos tocados: `README.md`, `harness-conf/AGENTS.base.md`,
`harness-conf/opencode.json`, `tests/test_opencode_plugins.py`.
Veredicto: OK (nenhum arquivo em src/ ou adapters/ aparece no commit).

### 1041452: test(integration): valida spawn dinamico com modelos distintos via task

```
 tests/integration/test_task_model_spawn.py | 357 +++++++++++++++++++++++++++++
 1 file changed, 357 insertions(+)
```

Arquivos tocados: `tests/integration/test_task_model_spawn.py`.
Veredicto: OK (nenhum arquivo em src/ ou adapters/ aparece no commit).

Verificação dos commits do plugin: CONFIRMADA. Os três commits (0f1ce5e,
cdde56f, 1041452) tocam apenas `harness-conf/`, `README.md` e `tests/`;
nenhum arquivo de `src/` ou `adapters/` aparece neles.

### 795e284: fix(harness): ajusta modos e permissoes de agentes para spawn via task

```
 docs/workflow-agentes-dev.md            |  4 ++++
 harness-conf/agents/analista.md         |  2 +-
 harness-conf/agents/curador-produto.md  |  3 ++-
 harness-conf/agents/dba.md              |  2 +-
 harness-conf/agents/devflow.md          |  1 +
 harness-conf/agents/eng-software.md     |  2 +-
 harness-conf/agents/front.md           |  2 +-
 harness-conf/agents/qa.md               |  2 +-
 harness-conf/agents/rev.md              |  2 +-
 harness-conf/agents/revisor-historia.md |  2 +-
 harness-conf/agents/sec.md              |  2 +-
 tests/agents/test_curador_produto.py    |  4 ++--
 12 files changed, 17 insertions(+), 11 deletions(-)
```

Arquivos tocados: `docs/workflow-agentes-dev.md`, 10 arquivos em
`harness-conf/agents/` (analista, curador-produto, dba, devflow,
eng-software, front, qa, rev, revisor-historia, sec) e
`tests/agents/test_curador_produto.py`.
Veredicto: registrado (nenhum arquivo em src/ ou adapters/; a alteração de
`src/` fica no commit seguinte, 94d33f6).

### 94d33f6: fix(harnesses): espelha semantica de modos no adapter copilot

```
 src/opencode_config/harnesses/copilot.py  |  76 ++++++++++++++-
 tests/agents/test_task_spawnable_modes.py | 148 ++++++++++++++++++++++++++++++
 tests/harnesses/test_copilot.py           | 114 +++++++++++++++++++++--
 3 files changed, 331 insertions(+), 7 deletions(-)
```

Arquivos tocados: `src/opencode_config/harnesses/copilot.py`,
`tests/agents/test_task_spawnable_modes.py` (novo) e
`tests/harnesses/test_copilot.py`.
Veredicto: OK (o commit altera `src/opencode_config/harnesses/copilot.py`,
exatamente como o insumo registra).

### 6a65b34: fix(harness): reverte analista para agente primario nao mediado

```
 docs/workflow-agentes-dev.md              |  4 ++--
 docs/workflow-definicao-escopo.md         |  7 +++++--
 harness-conf/agents/analista.md           |  2 +-
 harness-conf/agents/devflow.md            |  1 -
 tests/agents/test_task_spawnable_modes.py |  6 +++---
 5 files changed, 11 insertions(+), 9 deletions(-)
```

Arquivos tocados: `docs/workflow-agentes-dev.md`,
`docs/workflow-definicao-escopo.md`, `harness-conf/agents/analista.md`,
`harness-conf/agents/devflow.md` e
`tests/agents/test_task_spawnable_modes.py`.
Veredicto: registrado (nenhum arquivo em src/ ou adapters/; a reversão do
analista para `mode: primary` é consistente com o insumo).

## Estado do worktree (registro, leitura only)

O worktree está sujo com trabalho alheio em andamento, não reportado a esta
execução. A baseline não tocou em nenhum destes arquivos:

```
 M AGENTS.md
 M README.md
 M adapters/opencode/README.md
 M build.gradle
 M docs/adr/diagrama-c4-l1.md
 M docs/adr/diagrama-c4-l2.md
 M docs/adr/diagrama-c4-l3.md
 M harness-conf/commands/sync-upstream-skills.md
 M harness-conf/skills/writing-for-agents/UPSTREAM.md
 M plan/insumo-devflow-spawn-dinamico.md
 M plan/otimizacao-custo-contexto.md
 M src/opencode_config/cli/skills_sync.py
 M tests/product_tests/test_concordion_spec_infra.py
 M tests/skills_mgmt/test_sync.py
?? docs/adr/0007-deteccao-read-only-upstream-skills.md
?? src/test/groovy/Adr0007Fixture.groovy
?? tests/agents/test_sync_upstream_command.py
?? tests/skills_mgmt/test_detect.py
```

O arquivo `?? tests/skills_mgmt/test_detect.py` é a causa do erro de coleção
do item 1. Os commits recentes do repo (c011228, c93d813, fce5144, 68138ef,
9b185cb, b416dbe, 6ed2257, 010ebe1) são posteriores à leva revalidada e ficam
fora do escopo desta baseline.

## Evidências (eng-software)

- [x] Suíte completa executada sem seleção reduzida (resultado: erro de
      coleção, registrado no item 1).
- [x] Testes de consistência executados: 24/24 passed, 0 failed, 0 skipped.
- [x] `git show --stat` executado para os 6 commits; veredictos registrados
      no item 3.
- [x] Nenhum arquivo alterado fora desta evidência; nenhum commit criado.
