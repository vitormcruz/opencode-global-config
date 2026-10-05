# Skill agent-introspection-debugging + rename harness-skills

Status: TESTES

## Insumo do humano (cronologia)

1. Pesquisar estratégias para evitar requisições LLM desnecessárias pelo
   agente (ex.: reler arquivo em faixas repetidas, cada leitura virando
   uma requisição).
2. Aprovar importação da skill `agent-introspection-debugging` do repo
   GitHub `affaan-m/ECC` (commit `d29cf651c795869f733669c33e3d33dfd8307d10`)
   como uso global (todos os projetos, ambos os harnesses).
3. Corrigir premissa: o repo é multi-harness (OpenCode + Copilot CLI);
   a manutenção da skill precisa entrar no mecanismo de sync do CLI.
4. Verificar aderência aos mecanismos existentes: detecção de mudança
   upstream e roteamento global/domínio do adapter Copilot.
5. Renomear o comando `opencode-skills` para `harness-skills` (nome velho).
6. Organizar todo o trabalho pelo workflow (este plano).

## Decisões registradas

- Skill classificada como global: sem entrada no deny de
  `harness-conf/opencode.json` + incluída na whitelist `_GLOBAL_SKILLS`
  em `tests/agents/test_workflow_consistency.py`. Adapter Copilot a
  materializa em `~/.copilot/skills`.
- `SKILL.md` é adaptação PT-BR e nunca é sobrescrito pelo sync (padrão do
  repo: `_copy_skill_md` só copia na criação inicial).
- Sync da família ECC copia apenas `LICENSE` e regenera o `UPSTREAM.md`;
  detecção de mudança restrita ao subpath
  `skills/agent-introspection-debugging/` (repo upstream grande).
- Família sem handler conhecido agora levanta `SyncError` (antes: fallback
  para handler de outra família, que contaminava LICENSE/references e
  regenerava UPSTREAM.md apontando para o repo errado).
- Rename completo do comando, sem alias: 36 arquivos, zero referências ao
  nome velho; pacote reinstalado em user-space; symlink velho removido.
- Nada commitado ainda (checkpoint de commit pendente).

## Trabalho já executado (fora do workflow)

Arquivos novos:
- `harness-conf/skills/agent-introspection-debugging/SKILL.md`
  (adaptado PT-BR; triggers PT+EN; linha extra "Mesmo arquivo lido em
  faixas diferentes" na tabela de diagnóstico).
- `harness-conf/skills/agent-introspection-debugging/UPSTREAM.md`
  (formato padrão; arquivos sincronizados: LICENSE;
  `description_lang: ptbr`).
- `harness-conf/skills/agent-introspection-debugging/LICENSE` (MIT do ECC).
- `tests/skills/test_agent_introspection_debugging.py` (12 testes).
- `tests/skills_mgmt/test_agent_introspection_family.py`.

Arquivos alterados:
- `src/opencode_config/cli/skills_sync.py`: cadastro da família ECC no
  SPECS; branch monorepo em `_skill_diff_paths`; handler
  `_sync_agent_introspection_debugging`; dispatch com `else: raise
  SyncError`; textos/help com nome novo `harness-skills`.
- `pyproject.toml`: entrypoint renomeado para `harness-skills`.
- `tests/agents/test_workflow_consistency.py`: whitelist `_GLOBAL_SKILLS`.
- `tests/harnesses/test_copilot.py`: contadores 11 globais / 23 domínios.
- `AGENTS.md`: linha nova na tabela de sync + rename.
- `README.md`, `adapters/opencode/README.md`,
  `harness-conf/commands/sync-upstream-skills.md`,
  `docs/adr/0007-deteccao-read-only-upstream-skills.md`,
  `docs/specs/regras-negocio.md`, fixtures `build/` e `src/test/groovy/`:
  rename `opencode-skills` → `harness-skills`.
- 17 arquivos `UPSTREAM.md` das skills: comandos documentados renomeados
  (o `update` parseia esses comandos).

## Estado de validação

- Suíte completa verde no ambiente corrente: `.venv/bin/pytest -m all`
  → 958 passed, 31 deselected (agent_eval exige Docker + llama-server).
- `harness-skills detect agent-introspection-debugging` real contra o
  GitHub: "sem mudanças na família".
- `harness-skills list` mostra a skill nova; `--check-only` valida LICENSE.

## Fases restantes (proposto)

1. REVISÃO DA CONSTRUÇÃO: `rev` (instância limpa) revisa o construído com
   skills de domínio; achados → especialista; resubmissão controlada pelo
   humano.
2. Commit checkpoint pelo `eng-software` (único committer) após revisão.
3. TESTES: `qa` roda agregador `testes-produto` + roteiros do plano;
   `sec` roteiro manual; `curador-produto` valida evidência.
4. FINALIZAÇÃO: `curador-produto` revisa artefatos de spec; encerramento
   com autorização humana (excluir plano?).

## Mapa de modelos (combinado com o humano)

- Revisão: `zai-coding-plan/glm-5.3`.
- Execução (correções) e testes: glm 5.3 flash (ref exata a resolver na
  primeira chamada dessas fases).

## Perguntas

1. Ponto de entrada retroativo: decidido — REVISÃO DA CONSTRUÇÃO.
2. Mapa de modelos: decidido (acima).
3. Checkpoint de commit: decisão do orquestrador — após a revisão da
   construção e aplicação de correções, pelo `eng-software`, antes dos
   testes.

## Revisão da Construção

Revisor: `rev` (instância limpa, skill `code-review-and-quality`).
Escopo: lote não commitado inteiro (`git diff HEAD` + não rastreados).
Data: 2026-10-04. Leituras e comandos somente leitura; nenhuma suíte
executada; nenhum arquivo do lote alterado.

### Verificações aprovadas (sem achado)

- Invariante SKILL.md: `_sync_agent_introspection_debugging` não chama
  `_copy_skill_md`; nenhuma linha do handler copia SKILL.md. Teste
  `test_sync_copies_license_and_preserves_adapted_skill_md` reforça.
- Dispatch: as 7 famílias de `SPECS` possuem handler explícito; o
  `else: raise SyncError` não afeta famílias existentes e elimina o
  fallback silencioso entre famílias.
- Parse do `update`: os 17 `UPSTREAM.md` renomeados preservam indentação
  de 4 espaços na seção "## Como atualizar" (diffs só trocaram as duas
  linhas de comando); `harness-skills` está na whitelist
  `_DOCUMENTED_EXECUTABLES`; cada arquivo gera exatamente 1 comando de
  update + 1 de check-only (sem ambiguidade em `update_skill`).
- Rename: nenhuma referência a `opencode-skills`/`opencode_skills` como
  texto de comando em arquivos versionados (grep no repo). Docs
  (README, adapters/opencode/README, command de sync, ADR-0007,
  RN-006, fixture Groovy, infra Concordion) descrevem o comportamento
  real do CLI renomeado; `pyproject.toml` com entrypoint novo.
- Skill importada: frontmatter válido (name + description com triggers
  PT e EN), adaptação PT-BR coerente, sem referências pendentes ao ECC
  (guardado por teste), linhas até 120 colunas (awk sem achados em todo
  o lote MD; a skill tem teste próprio de largura). Pasta contém
  exatamente SKILL.md, UPSTREAM.md e LICENSE, consistente com
  "Arquivos sincronizados: LICENSE".
- Roteamento global: `agent-introspection-debugging` sem entrada deny em
  `harness-conf/opencode.json`; `_GLOBAL_SKILLS` com 11 entradas
  confere com o contador 11 globais do teste do adapter Copilot.
- Testes: markers `unit`/`integration` conforme ADR-0005, sem `skip`
  nos arquivos novos; estrutura espelhada em `tests/skills/` e
  `tests/skills_mgmt/`.
- `build/` é gitignored (linha 29 do .gitignore): fixtures de build
  citadas no plano não são versionadas, nada a revisar no disco.

### Achados

| # | Achado | Ação recomendada | Severidade | Especialista |
|---|--------|------------------|------------|--------------|
| 1 | Inconsistência detect × sync: `_skill_diff_paths` da família ECC restringe o diff a `skills/agent-introspection-debugging/`, mas o handler copia `LICENSE` da raiz do upstream. Uma mudança no LICENSE upstream não é sinalizada pelo `detect`, embora o `sync` a aplicaria silenciosamente. | Incluir o path raiz `LICENSE` no pathspec da família (ou deixar de copiar LICENSE no sync) e adicionar teste de detect cobrindo mudança de LICENSE. | média | eng-software |
| 2 | Lacuna de evidência de segurança: AGENTS.md exige revisão de segurança na importação (ler todo o conteúdo copiado); humanizer-br e portugues-tecnico-controlado registram o veredito no UPSTREAM.md, mas o UPSTREAM.md novo não registra nada. Nota do rev: li integralmente SKILL.md, UPSTREAM.md e LICENSE e não encontrei prompt injection, comandos, URLs ou exfiltração; falta apenas o registro formal. | Registrar o veredito da revisão de segurança no UPSTREAM.md, em seção preservada pela regeneração (dentro de "## Adaptacao da description" ou "## Notas locais"). | média | sec |
| 3 | Inconsistência de metadados: skills convertidas gravam campo top-level `description_lang: pt-br` via `extra_fields` no handler (portugues-tecnico-controlado, writing-for-agents, humanizer-br); a nova grava `description_lang: ptbr` só dentro da seção "## Adaptacao da description" e o handler não passa `extra_fields`, então após um sync o layout diverge das irmãs e o valor usa `ptbr` em vez de `pt-br`. O teste `test_upstream_documents_ptbr_description_decision` fixa o valor divergente. | Alinhar handler (passar `extra_fields=["description_lang: pt-br"]`), UPSTREAM.md e o teste ao valor `pt-br`; manter a nota da decisão na seção de adaptação. | baixa | eng-software |
| 4 | Lacuna de cobertura: o branch `else: raise SyncError("Upstream sem handler...")` introduzido neste lote não tem teste. O comportamento substituiu um fallback silencioso defeituoso e merece guarda de regressão: spec nova sem handler deve falhar, nunca cair em handler de outra família. | Adicionar teste unitário injetando spec desconhecida no dispatch e asserting `SyncError`. | baixa | eng-software |
| 5 | Desvio de nomenclatura: identificadores de teste mantêm o nome velho, apesar de o plano registrar "zero referências ao nome velho": `test_opencode_skills_entrypoint_is_registered` (tests/skills_mgmt/test_sync.py:38) e `test_skill_registrada_no_opencode_skills` (tests/skills/test_writing_for_agents.py:86). Não é texto de comando, mas perpetua o nome antigo na suíte. | Renomear os identificadores (cosmético; atualizar referências de node id se houver). | baixa | eng-software |
| 6 | Desvio de ambiente: o `.venv` (interpretador mandatório dos testes) tem instalação editável com entry point desatualizado: `.venv/bin/opencode-skills` existe e `.venv/bin/harness-skills` não. O código resolve para src (editable .pth), mas os comandos documentados `harness-skills` não ficam disponíveis dentro do `.venv` sem o fallback `python -m`. | Reinstalar o pacote no `.venv` (`pip install -e .`) para regenerar os entry points; remover o script velho. Ambiente local, não versionado. | baixa | eng-software |
| 7 | Robustez: `_sync_agent_introspection_debugging` é o único handler que não garante `local_skill.mkdir` antes de `shutil.copy2` (os demais passam por `_copy_skill_md`, que cria o diretório). Se o diretório da skill estiver ausente, o erro é `FileNotFoundError` genérico em vez de `SyncError` claro. | Criar o diretório (ou reutilizar `_copy_skill_md` como guarda) antes de copiar LICENSE. | baixa | eng-software |

### Veredicto

[ ] Aprovado sem ressalvas
[x] Aprovado com melhorias opcionais
[ ] Bloqueado — resolver achados bloqueantes antes de prosseguir

Nenhum achado alta/bloqueante. Recomenda-se resolver os achados 1 e 2
antes do checkpoint de commit; os de severidade baixa podem seguir como
fila para o `eng-software` no mesmo lote ou no próximo.

### Evidências (rev)

- [x] Artefatos lidos: plano, AGENTS.md, `src/opencode_config/cli/skills_sync.py`
      (inteiro + diff), SKILL.md, UPSTREAM.md e LICENSE da skill nova,
      `tests/skills/test_agent_introspection_debugging.py`,
      `tests/skills_mgmt/test_agent_introspection_family.py`,
      `tests/skills_mgmt/test_sync.py` (trechos), diffs de docs, tests e
      UPSTREAM.md renomeados, `harness-conf/opencode.json` (deny).
- [x] Plano aprovado consultado: sim (seções Decisões, Trabalho
      executado e Estado de validação).
- [x] Checklist integrativo: 9 dimensões (mecanismo de sync, rename
      código↔docs, qualidade da skill, cobertura de testes, regras de
      teste do repo, largura de linha, roteamento global, evidência de
      segurança, ambiente).
- [x] Achados encontrados: 7 total, 0 alta (bloqueante), 2 média,
      5 baixa.
- [x] Comandos: somente leitura (`git status/diff`, `grep`, `awk`,
      `ls`, `git check-ignore`); nenhuma suíte executada.

## Correções da Revisão da Construção

Execução: `eng-software`, 2026-10-04. TDD: testes primeiro, RED
confirmado (3 falhas esperadas), depois GREEN. Mudança de spec nos
testes dos achados 2 e 1 (asserções existentes) aprovada pelo humano
via relatório de revisão e briefing do lote.

| # | Severidade | Ação aplicada | Arquivos |
|---|-----------|---------------|----------|
| 1 | média | Pathspec da família ECC vigia também o LICENSE raiz copiado pelo sync; teste novo de detect (fixture git local) prova que mudança no LICENSE raiz aparece no relatório | `src/opencode_config/cli/skills_sync.py`; `tests/skills_mgmt/test_agent_introspection_family.py` |
| 2 | média | Registro da revisão de segurança da importação gravado pelo `sec` em seção preservada (`## Notas locais`), com data, escopo, método, veredito (limpo) e recomendação de revisar diff a cada sync | `harness-conf/skills/agent-introspection-debugging/UPSTREAM.md` |
| 3 | baixa | `description_lang: pt-br` top-level: handler passa `extra_fields`; UPSTREAM.md realinhado (campo no cabeçalho, nota mantida na seção de adaptação); teste atualizado | `src/opencode_config/cli/skills_sync.py`; `harness-conf/skills/agent-introspection-debugging/UPSTREAM.md`; `tests/skills/test_agent_introspection_debugging.py` |
| 4 | baixa | Teste novo: spec injetada sem handler conhecido levanta `SyncError` (guarda do branch `else` do dispatch) | `tests/skills_mgmt/test_sync.py` |
| 5 | baixa | Identificadores de teste renomeados para o nome novo do comando | `tests/skills_mgmt/test_sync.py`; `tests/skills/test_writing_for_agents.py` |
| 6 | baixa | `pip install -e .` regenerou os entry points; `opencode-skills` removido do `.venv/bin`; `harness-skills list --help` verificado | ambiente (`.venv`, não versionado) |
| 7 | baixa | `local_skill.mkdir(parents=True, exist_ok=True)` antes do `copy2` do LICENSE | `src/opencode_config/cli/skills_sync.py` |

- Notas locais do sec preservadas: `_write_upstream` mantém as seções
  `## Notas locais` e `## Adaptacao da description` na regeneração
  (extração por regex antes da reescrita); arquivo conferido após as
  edições.
- Suíte completa: `.venv/bin/pytest -m all` → 960 passed, 31 deselected
  (agent_eval exige Docker). Baseline 958 + 2 testes novos.

### Evidências de Testes — Correções da Revisão

- [x] Testes novos: 2 (detect LICENSE raiz, dispatch sem handler). O de
      detect falhou antes do código (RED confirmado). O de dispatch é
      guarda de comportamento já implementado: passou de imediato, por
      desenho (o achado pedia cobertura, não código novo).
- [x] Testes totais: 960 executados, 960 passed, 31 deselected.
- [x] Análise estática: ruff, all checks passed nos 5 arquivos tocados.
- [x] Regressão incremental: módulos tocados reexecutados a cada passo
      (74 passed) antes da suíte completa.
- [x] Gate de refatoração: cenário "nada muda"; refatoração sem impacto
      no plano.

## Revisão das Correções

Revisor: `rev` (instância nova, skill `code-review-and-quality`).
Objeto: correções declaradas na seção anterior, verificadas nos commits
`34e05d2` (código+testes+skill) e `94c5c45` (plano) via `git show` e leitura
dos arquivos em HEAD. Data: 2026-10-05.

### Veredicto por achado da Revisão da Construção

| # | Achado original | Veredicto | Evidência curta |
|---|-----------------|-----------|-----------------|
| 1 | detect não vigiava o LICENSE raiz (média) | resolvido | `_skill_diff_paths` da família ECC retorna `("skills/{nome}/", "LICENSE")`; teste `test_detect_reports_change_in_root_license` (fixture git local) sinaliza mudança do LICENSE raiz no detect |
| 2 | registro da revisão de segurança ausente (média) | resolvido | UPSTREAM.md tem `## Notas locais` com `### Revisão de segurança da importação` (data, escopo, método, veredito); `_write_upstream` extrai e reanexa `_local_notes_section`, então a seção sobrevive à regeneração |
| 3 | `description_lang` divergente das irmãs (baixa) | resolvido | handler passa `extra_fields=["description_lang: pt-br"]`; UPSTREAM.md linha 5 com o campo top-level; `test_upstream_documents_ptbr_description_decision` agora checa o cabeçalho |
| 4 | branch `else: raise SyncError` sem teste (baixa) | resolvido | `test_sync_rejects_family_without_known_handler` injeta spec desconhecida no dispatch e espera `SyncError` com "sem handler" |
| 5 | identificadores de teste com nome velho (baixa) | resolvido | `test_harness_skills_entrypoint_is_registered` (tests/skills_mgmt/test_sync.py:38) e `test_skill_registrada_no_harness_skills` (tests/skills/test_writing_for_agents.py:86); `git grep` em rastreados sem `opencode-skills`/`opencode_skills` fora de plan/ |
| 6 | entrypoint do `.venv` desatualizado (baixa) | resolvido | `.venv/bin/harness-skills` existe e executa `list --help`; `.venv/bin/opencode-skills` ausente |
| 7 | `mkdir` ausente antes do `copy2` (baixa) | resolvido | `local_skill.mkdir(parents=True, exist_ok=True)` imediatamente antes de `shutil.copy2` do LICENSE no handler |

### Achados desta revisão

| # | Achado | Ação recomendada | Severidade |
|---|--------|------------------|------------|
| 1 | Desvio de documentação no plano: a tabela "Correções da Revisão da Construção" omite a linha do achado 2 (registro da revisão de segurança) e numera as demais de 1 a 6, desalinhada dos achados originais 1 a 7. A correção em si foi aplicada e verificada no UPSTREAM.md e no commit `34e05d2`; é apenas o registro na tabela que ficou incompleto. | Renumerar a tabela para 7 linhas conforme os achados originais na próxima edição do plano pelo eng-software | melhoria |

Resolução: tabela renumerada para 7 linhas (achado 2 incluído como linha do `sec`)

### Regressão

- Suíte completa executada pelo rev (autorizado na tarefa):
  `.venv/bin/pytest -m all` → 960 passed, 31 deselected (agent_eval exige
  Docker), 1 warning, 201s. O warning é o monitor de flutuação do plugin
  `@slkiser/opencode-quota` (4.10.6 → 5.0.1), pré-existente e alheio a
  este lote.
- Testes existentes não enfraquecidos: os diffs de `34e05d2` trocam nome do
  executável e identificadores sem relaxar asserções (conferido linha a
  linha no diff de testes).
- Seções `## Notas locais` e `## Adaptacao da description` preservadas no
  UPSTREAM.md em HEAD; largura até 120 colunas conferida nos 7 arquivos
  tocados (awk sem achados).
- Imports e sintaxe íntegros (suíte verde cobre os módulos tocados).

### Veredicto

[ ] Aprovado sem ressalvas
[x] Aprovado com melhorias opcionais — 7/7 achados resolvidos, sem regressão;
    1 achado novo de documentação do plano (melhoria, não bloqueante)
[ ] Bloqueado — resolver achados bloqueantes antes de prosseguir

### Evidências (rev)

- [x] Artefatos lidos: plano (Revisão da Construção e Correções), diffs dos
      commits `34e05d2` e `94c5c45`, `src/opencode_config/cli/skills_sync.py`
      (handler, `_write_upstream`, `_skill_diff_paths`, dispatch), UPSTREAM.md
      da skill, 4 arquivos de teste tocados.
- [x] Plano aprovado consultado: sim.
- [x] Checklist integrativo: verificação ponto a ponto dos 7 achados +
      checagem de regressão (suíte, rename versionado, largura de linha,
      preservação de seções do UPSTREAM.md, ambiente `.venv`).
- [x] Achados desta revisão: 1 total (documentação do plano), 0 bloqueantes.
- [x] Comandos: `git show`, `git grep`, `grep`, `awk`, `ls`, execução do
      entrypoint `.venv/bin/harness-skills list --help`; suíte completa
      executada uma única vez.

## Evidências da Fase de Testes

Executor: `qa`. Data/hora: 2026-10-05 08:45 (-03). Ambiente: WSL/Linux,
Python 3.12.3 (`.venv`). Objeto do lote: importação da skill
`agent-introspection-debugging` + rename `opencode-skills` →
`harness-skills` + correções de revisão (commits `34e05d2`, `94c5c45`).

### 1. Suíte completa do repo

- Comando: `.venv/bin/pytest -m all -q`, seleção integral do ambiente
  corrente (nenhuma redução).
- Resultado: 960 passed, 0 failed, 31 deselected, 1 warning, 186.64s
  (0:03:06).
- Deselected: `-m agent_eval` (exige Docker + llama-server local
  Qwen3-0.6B), deselect de ambiente declarado na ADR-0005, não lacuna do
  lote. Nenhum `skip` simples apareceu no relatório.
- Warning: monitor de flutuação do plugin `@slkiser/opencode-quota`
  (4.10.6 → 5.0.1), pré-existente, alheio ao lote, já registrado na
  revisão anterior.
- Convergente com as duas execuções anteriores do lote (960 passed).

### 2. Bateria por especialidade (`testes-produto`)

- Investigação: o agregador (`src/opencode_config/product_tests/
  aggregator.py`) executa as suítes `backend` e `seguranca`:
  - backend: suíte pytest completa com gate de cobertura
    (`--cov-fail-under=70`), ruff em src/scripts/testes-produto,
    shellcheck (*.sh), PSScriptAnalyzer (*.ps1) e specs Concordion
    backend;
  - seguranca: gitleaks (segredos), pip-audit (dependências do `.venv`),
    bandit (SAST) e specs Concordion seguranca.
- Decisão de aplicabilidade — AMBAS se aplicam (lote de infra de repo:
  CLI + skill + docs):
  - backend: o lote altera código Python produtivo
    (`src/opencode_config/cli/skills_sync.py`), entrypoint no
    `pyproject.toml` e testes; gate de cobertura, lint e specs Concordion
    backend se aplicam diretamente.
  - seguranca: o lote importa conteúdo externo (skill do repo ECC) e toca
    `src/`; varredura de segredos, auditoria de dependências e SAST são
    gates de repo inteiro. A revisão de segurança manual do conteúdo
    importado já foi feita pelo `sec` (registrada no UPSTREAM.md); aqui
    rodou apenas a suíte automática, papel do `testes-produto`.
- Execução: `.venv/bin/python testes-produto` (modo checkout, conforme
  `testes-produto/README.md`) → exit 0, status `pass`.
  - Findings: 1 `melhoria` (bandit:
    `src/opencode_config/bootstrap/ai_memory.py:941`, "Audit url open for
    permitted schemes"), pré-existente, fora do lote, não bloqueante.
  - Zero findings bloqueantes; gate de cobertura 70% atendido (exit 0).
- Suíte meta `testes-produto/tests/`: não aplicável — roda somente quando
  os scripts de `testes-produto/` mudam; este lote não os tocou (justified,
  não omissão silenciosa).

### 3. Smoke do CLI renomeado

- `harness-skills list` (user-space `~/.local/bin`): OK, 17 skills,
  `agent-introspection-debugging` presente.
- `harness-skills detect --help`: OK; usage lista
  `agent-introspection-debugging` entre as 7 famílias de sync.
- `.venv/bin/harness-skills list`: OK, mesma lista de 17 skills.
- `.venv/bin/opencode-skills`: inexistente (confirmado com `test -e`).

### Veredicto da fase

APROVADO. Suíte completa verde em terceira execução convergente; bateria
por especialidade pass sem achado bloqueante; smoke do rename OK.

### Evidências (qa)

- [x] Plano de testes: roteiro da fase executado conforme tarefa (suíte
      integral + baterias por especialidade + smoke); nenhum teste manual
      adicional planejado (nenhuma UI/RNF no escopo).
- [x] Testes executados: 960 passed, 0 failed, 31 deselected (agent_eval/
      Docker) + agregador `testes-produto` (backend + seguranca) exit 0.
- [x] Cobertura: gate `--cov-fail-under=70` atendido no agregador; delta
      numérico vs. baseline não mensurado (baseline não registrado no
      plano).
- [x] Cenários não cobertos: nenhum novo; `-m agent_eval` é deselect de
      ambiente declarado, e a suíte meta não se aplica (scripts não
      mudaram).
- [x] Falhas a reportar: nenhuma (nenhum bloqueante; 1 melhoria bandit
      pré-existente, fora do lote).

### Validação do curador

Veredito: EVIDÊNCIA VÁLIDA (validação documental, sem reexecução;
2026-10-05, curador-produto).

- Completude: suíte completa com comando, counts (960 passed, 0 failed,
  31 deselected), tempo e warning justificado; agregador com comando,
  exit 0, status `pass` e gate de cobertura 70% atendido; smoke do CLI
  com 4 checagens e resultados. Quem não executou nada consegue
  reconstituir o que rodou, quando (2026-10-05 08:45 -03) e em qual
  ambiente (WSL/Linux, Python 3.12.3, `.venv`).
- Decisões: aplicabilidade de backend e seguranca justificada (código
  Python produtivo; conteúdo externo importado, gates de repo inteiro);
  suíte meta justificada como não aplicável (scripts de `testes-produto/`
  não mudaram no lote).
- Consistência: 960 passed coerente nas três execuções do lote
  (correções, revisão das correções, fase de Testes), com baseline 958 +
  2 testes novos documentado; findings do agregador coerentes com o spec
  de `docs/README.md#testes-por-especialidade` (bandit severidade média =
  melhoria, não bloqueante; gate de cobertura = 70% bloqueante).
- Rastreabilidade: todos os comandos citados na evidência.
- Observação (melhoria, não invalida): em "Evidências (qa)", o item
  Cobertura diz "baseline não registrado no plano"; no contexto, refere-se
  ao percentual de cobertura (de fato ausente do plano). O baseline de
  testes (958 → 960) está registrado. Redação ambígua, sem impacto no
  veredicto.
