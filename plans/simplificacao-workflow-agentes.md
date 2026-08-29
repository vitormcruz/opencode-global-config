# Plano: Simplificação do Workflow Agêntico e Revisão de Skills/Prompts

Status: PLANEJAMENTO (smart-planner)

## Overview

Simplificar e aumentar a efetividade do workflow de desenvolvimento deste
repo (opencode-global-config), revisando a proposta anterior de simplificação
à luz de pesquisa atualizada sobre Agent Skills vs. contexto estático
(AGENTS.md/prompts). Direção evidenciada: contexto permanente mínimo com
âncoras explícitas para skills; skills como corpo sob demanda; redução de
camadas de orquestração.

## Decisões

- **D1 (resolvida)**: `devflow` **mantido** como roteador stateless. `eng-software`
  NÃO absorve a orquestração (opção (a) rejeitada; merge com workflow-agentico-simples
  também rejeitado). Ajustes derivados:
  - **Modo debug (DevFlowNotes): removido** (decisão humana).
  - **Seleção de modelo por fase: mantida** — humano fará experimentos com modelos
    diferentes por etapa (planejamento, execução, revisão).
  - Comitês de revisão: em discussão (ver Open Questions).
- **D2 (aprovada)**: especialistas são subagentes e **não commitam**. O operador
  (`eng-software`) é o único committer do workflow. Especialistas editam
  arquivos e reportam `[arquivos alterados + resumo ≤5 linhas]`.
  `git-workflow-and-versioning` deixa de ser obrigatória para especialistas.
- **D3 (aprovada, reformulada)**: NÃO extrair essência longa (15–30 linhas/skill)
  para prompts. Aplicar: regras invioláveis ≤10 linhas/agente no prompt +
  âncoras de 1 linha por skill (tabelas "carregue ANTES de…" já existentes).
  Fundamento: ETH Zurich (contexto sempre ativo inchado degrada, +20–23% custo)
  + Vercel (âncora explícita → trigger 95%+).
- **D4 (aprovada)**: unificar `curador-produto` + `curador-produto-editor` +
  `val-harness` num único agente final chamado **`curador-produto`** (nome
  mantido). Absorve edição de docs/README.md/harness e validação de evidências
  de harness. Regra de segurança: não valida na mesma fase o que editou.
- **D5 (aprovada)**: `rev` mantido como agente separado (olhar fresco,
  sem viés da construção).
- **D6 (aprovada)**: fim dos comitês de revisão (fases 3 e 5 do
  workflow-agentes-dev). O `rev` revisa sozinho, com **âncoras explícitas às
  skills de domínio** no prompt (security-and-hardening,
  frontend-ui-engineering, tests-as-spec, api-and-interface-design,
  documentation-and-adrs e a nova skill de modelagem de dados). Achados de
  domínio → `devflow` repassa ao especialista responsável corrigir.
  Justificativa: âncoras explícitas = padrão Vercel (trigger 95%+);
  revisão por checklist exige menos domínio que projetar.
- **D7 (aprovada)**: criar skill de modelagem de dados (domínio DBA) neste
  plano — fecha o buraco de competência do `rev` (opção A) e resolve a
  pendência nº 3 da proposta anterior.
- **D8 (aprovada)**: mecanismo de evidências de harness **mantido** (seção
  `## Evidências de Harness — <fase>` no arquivo de planejamento, por agente
  que alterou artefatos). Quem valida passa a ser o `curador-produto`
  unificado (substitui o `val-harness`), nas mesmas oportunidades: após
  Construção e Revisão da Construção.
- **D9 (aprovada)**: fase VALIDAÇÃO inicial **mantida**. Sem correção
  autônoma: setup de docs/README.md/harness é conversa complexa com o
  humano. Protocolo existente preservado (mensagens pré-definidas em
  `agents/references/mensagens-curadoria.md`, com referência atualizada de
  `curador-produto-editor` → `curador-produto`): devflow avisa e sugere ao
  humano conversar diretamente com o curador-produto; o humano pode optar
  por continuar o workflow mesmo assim.
- **D10 (aprovada)**: formalizar schema leve do arquivo de planejamento no
  workflow reescrito (seções obrigatórias: `Status`, `Regras de Produto`,
  `Evidências de Harness`, `Perguntas` — com ordem e formato definidos).
- **D11 (aprovada)**: criar teste pytest de consistência workflow↔agentes↔skills
  (falha se workflow citar agente/skill inexistente, ou agente citar skill
  inexistente). Sincronização manual vira verificação automática.
- **D12 (aprovada)**: escopo documental incluído — atualizar `README.md`,
  `AGENTS.md` do repo e `docs/workflow-curadoria.md` onde citam agentes
  removidos/modificados.
- **D13 (aprovada, com refinamentos)**: trabalho de curadoria integrado ao
  workflow dev (emenda a D9 — fim da mediação direta humano↔curador):
  - Gate na fase 1: curador verifica docs/README.md + harness; se houver
    lacuna/problema, `devflow` pergunta ao humano se quer tratar agora.
    Sim → as fases de dev conduzem o trabalho de curadoria. Não → o
    desenvolvimento segue com a lacuna registrada no planning file.
  - Todos os passos de curadoria preservados como conteúdo (bootstrap,
    revisão item a item, spec de harness) — agora conduzidos pelas fases
    de dev, antes de qualquer planejamento de funcionalidade.
  - Curador simplificado: foco em deixar a especificação de produto
    (docs/README.md) e o harness bem feitos. **Sem orquestração de
    conversa própria** — a mediação (quando juntar/separar perguntas,
    ritmo, aprovações) é responsabilidade do `devflow`.
  - Harness do trabalho de curadoria: `eng-software` roda os harness
    implementados ao final; o curador verifica o sucesso (verde) —
    validação objetiva que resolve a regra "não valida o que editou".
  - `docs/workflow-curadoria.md` **extinto**: conhecimento migra para o
    prompt do curador + `agents/references/` + skill `harness-catalog`.
    `docs/workflow-definicao-escopo.md` intacto, só com referências
    atualizadas (editor → curador-produto; sem modo debug).
  - Participações posteriores do curador no ciclo inalteradas (D8:
    validação de evidências; fase 7: revisão final).

## Visão final aprovada

- Agentes: 14 → 12 (removidos `curador-produto-editor` e `val-harness`;
  `curador-produto` unificado absorve ambos; `devflow` mantido como roteador).
- Workflows dev: `workflow-curadoria.md` extinto (D13 — trabalho de
  curadoria conduzido pelas fases de dev, com gate na fase 1); restam
  `workflow-agentes-dev.md`, `workflow-definicao-escopo.md` e
  `workflow-agentico-simples.md` (não-dev).
- Revisões de plano e construção: `rev` sozinho com âncoras às skills de
  domínio; achados voltam via `devflow` ao especialista; rev não corrige.
- Commits: `eng-software` é o único committer do workflow, sem exceções
  (D13 removeu o modo direto de setup do curador).
- Curador-produto: foco em conteúdo (especificação de produto e harness);
  sem orquestração de conversa — mediação é do `devflow`.
- Prompts: âncoras de 1 linha por skill (já existentes) + regras
  invioláveis ≤10 linhas/agente; sem extração de essência longa.

## Task List

### Phase 0 — Infra do experimento

- [ ] **Task 0: Adapter Copilot ignora `worker` e `revisor`**
  **Description**: `agents/worker.md` e `agents/revisor.md` já foram criados
  (infra de orquestração do experimento, globais no OpenCode via symlink,
  com `model` editável no frontmatter). O adapter Copilot copia
  `agents/*.md` indiscriminadamente — adicionar mecanismo de exclusão
  explícito em `src/opencode_config/adapters/copilot.py` (lista de agentes
  OpenCode-only) + testes em `tests/adapters/`.
  **Acceptance criteria**:
  - [ ] `_sync_agents` exclui `worker.md` e `revisor.md` (lista nomeada, não regex genérica)
  - [ ] Teste cobre: agentes excluídos não copiados; demais inalterados
  **Verification**: `.venv/bin/pytest tests/adapters/ -k copilot` passa
  **Dependencies**: None
  **Files**: `src/opencode_config/adapters/copilot.py`, `tests/adapters/test_copilot_adapter.py`
  **Estimated scope**: S

### Phase 1 — Fundação: skill DBA e curador unificado

- [ ] **Task 1: Criar skill `data-modeling` (domínio DBA)**
  **Description**: nova skill autoral em `skills/data-modeling/SKILL.md`,
  PT-BR, seguindo o padrão das skills locais (ex.: `clean-code`). Corpo:
  modelagem conceitual/lógica, normalização, tipos e constraints, migrações
  seguras, indexação, lock/zero-downtime, checklist de revisão de artefatos
  de BD. Description (frontmatter) com "o que faz + quando usar" + keywords
  de gatilho (modelagem, schema, migration, migração, normalização, índice,
  FK, zero-downtime). Sem `UPSTREAM.md` (skill autoral, não externa).
  **Acceptance criteria**:
  - [ ] `skills/data-modeling/SKILL.md` existe, ≤400 linhas, PT-BR com acentuação
  - [ ] Description contém gatilhos explícitos de ativação
  - [ ] Checklist de revisão de modelo/migration incluído (para o `rev` usar)
  - [ ] Testes em `tests/skills/` seguindo padrão dos testes de skills existentes
  **Verification**: `.venv/bin/pytest tests/skills/ -k data_modeling` passa
  **Dependencies**: None
  **Files**: `skills/data-modeling/SKILL.md`, `tests/skills/test_data_modeling.py`
  **Estimated scope**: M

- [ ] **Task 2: Unificar e simplificar curador-produto (absorve editor + val-harness)**
  **Description**: reescrever `agents/curador-produto.md` como agente
  unificado com foco em CONTEÚDO (não em orquestração de conversa —
  mediação é do devflow, D13): especificar docs/README.md (3 seções) e
  harness (catálogo `harness-catalog`, tetos, interface de harness que
  hoje vive no prompt do editor — mover detalhe extenso para
  `agents/references/`), editar artefatos quando spawnado, validar
  evidências de harness em lote (absorve `val-harness`: executar
  agregador do AGENTS.md e cruzar seção `## Evidências de Harness —
  <fase>`) e verificar sucesso (verde) dos harness implementados no
  trabalho de curadoria (D13). Regra de segurança: não valida mérito do
  que editou — validações dele são objetivas (presença/completude de
  evidências, execução verde de harness). Skills: obrigatória
  `documentation-and-adrs`; condicional `harness-catalog`. Nunca commita
  (subagente; eng-software é o committer). Remover
  `agents/curador-produto-editor.md` e `agents/val-harness.md` (usar
  `git rm`). Alvo ≤350 linhas.
  **Acceptance criteria**:
  - [ ] `agents/curador-produto.md` cobre os 3 papéis; ≤350 linhas
  - [ ] `agents/curador-produto-editor.md` e `agents/val-harness.md` removidos via `git rm`
  - [ ] `agents/references/mensagens-curadoria.md` atualizado (editor → curador-produto)
  - [ ] Template docs/README.md e interface de harness preservados (prompt ou `agents/references/`)
  - [ ] Sem roteiro de conversa no prompt (mediação é do devflow)
  **Verification**: grep não encontra `curador-produto-editor|val-harness` em `agents/`
  **Dependencies**: None
  **Files**: `agents/curador-produto.md`, `agents/curador-produto-editor.md`,
  `agents/val-harness.md`, `agents/references/mensagens-curadoria.md`,
  `agents/references/` (possível novo arquivo de template)
  **Estimated scope**: L (quebrar em sub-passos: 1-merge editor, 2-merge val-harness, 3-limpeza)

- [ ] **Task 3: Adaptar testes dos agentes fundidos**
  **Description**: adaptar `tests/agents/test_curador_produto_editor.py` e
  `tests/agents/test_val_harness.py` para o agente unificado (merge em um
  `test_curador_produto.py` novo ou ampliado). Manter assertions
  equivalentes das capacidades absorvidas.
  **Acceptance criteria**:
  - [ ] Testes do editor e val-harness migrados para o curador unificado
  - [ ] Nenhum teste referencia arquivos de agentes removidos
  **Verification**: `.venv/bin/pytest tests/agents/ -x` passa
  **Dependencies**: Task 2
  **Files**: `tests/agents/`
  **Estimated scope**: M

### Checkpoint: CP1 — commit `feat(agents): unificar curadoria no curador-produto e criar skill data-modeling`

- [ ] Testes de `tests/agents/` e `tests/skills/` passam
- [ ] `grep -r "curador-produto-editor\|val-harness" agents/ tests/` sem resultados

### Phase 2 — Especialistas, rev e eng-software

- [ ] **Task 4: Atualizar especialistas (dba, front, sec, qa)**
  **Description**: para cada um: remover `git-workflow-and-versioning` das
  obrigatórias (se ficar referência, vira âncora condicional de 1 linha);
  adicionar ao Contrato Operacional a regra de subagente: "não commitar;
  reportar `[arquivos alterados + resumo ≤5 linhas]` ao solicitante"; extrair
  regras invioláveis ≤10 linhas (D3 — ex. dba: "migration reversível ou
  plano de rollback"; front: "sem quebrar contrato visual aprovado"; sec:
  "segredo nunca em código"; qa: "teste aprovado é spec"). `dba` ganha
  âncora à skill `data-modeling` (obrigatória ao modelar).
  **Acceptance criteria**:
  - [ ] 4 agentes sem git-workflow como obrigatória e com regra de não-commit
  - [ ] Cada um com bloco "Regras invioláveis" ≤10 linhas
  - [ ] dba referencia `data-modeling`
  **Verification**: grep confirma ausência de "git-workflow" em obrigatórias; teste boilerplate passa
  **Dependencies**: Task 1
  **Files**: `agents/dba.md`, `agents/front.md`, `agents/sec.md`, `agents/qa.md`
  **Estimated scope**: M

- [ ] **Task 5: Atualizar `rev` para revisão solo com skills de domínio**
  **Description**: adicionar seção de skills condicionais de revisão com
  âncoras explícitas: `security-and-hardening` (ameaças), `data-modeling`
  (schema/migration), `frontend-ui-engineering` + `accessibility-audit`
  (UI), `tests-as-spec` (cobertura como spec), `api-and-interface-design`
  (contratos públicos), `documentation-and-adrs` (docs). Manter
  `code-review-and-quality` como obrigatória. Rev **não corrige**: reporta
  achados `achado · ação · severidade` e o `devflow` repassa ao
  especialista. Remover git-workflow; regra de não-commit; invioláveis
  ≤10 linhas (ex.: "read-only — nunca editar código em revisão").
  **Acceptance criteria**:
  - [ ] Tabela de âncoras às 6 skills de domínio no prompt do rev
  - [ ] Regra read-only/não-corrigir explícita
  - [ ] Formato de achados definido
  **Verification**: teste de boilerplate/consistência passa; grep confirma âncoras
  **Dependencies**: Task 1
  **Files**: `agents/rev.md`
  **Estimated scope**: S

- [ ] **Task 6: Ajustar `eng-software` (committer único)**
  **Description**: reforçar contrato: eng-software é o único committer do
  workflow — recebe relatórios dos especialistas, revisa as alterações
  deles (diff) e commita unidades lógicas seguindo
  `git-workflow-and-versioning` (mantém obrigatória para ele). Adicionar
  invioláveis ≤10 linhas (ex.: "nunca commitar sem testes verdes";
  "nunca commitar worktree com alterações alheias não reportadas").
  **Acceptance criteria**:
  - [ ] Papel de committer único explícito
  - [ ] Fluxo "revisar diff do especialista antes de commitar" descrito
  - [ ] Invioláveis ≤10 linhas
  **Verification**: teste boilerplate passa
  **Dependencies**: None
  **Files**: `agents/eng-software.md`
  **Estimated scope**: S

### Checkpoint: CP2 — commit `refactor(agents): especialistas nao commitam; rev revisa solo com skills de dominio`

- [ ] `.venv/bin/pytest -m "unit or tools"` passa
- [ ] Diffs revisados (sem alteração de comportamento além do contrato)

### Phase 3 — Orquestrador e workflows

- [ ] **Task 7: Reescrever `devflow`**
  **Description**: remover seção Modo Debug (~80 linhas); fases 3 e 5
  deixam de ter comitê: apenas `rev` (revisão solo) + repasse de achados ao
  especialista; validação de evidências de harness passa a spawnar
  `curador-produto` (não `val-harness`); manter seleção de modelo por fase e
  política de sessão; fase VALIDAÇÃO vira o gate da D13: curador verifica,
  devflow pergunta ao humano "tratar a curadoria agora?" — se sim, as fases
  de dev conduzem o trabalho de curadoria (antes de planejar
  funcionalidade); se não, segue com a lacuna registrada no planning file.
  Devflow assume a mediação do trabalho de curadoria (decide quando
  juntar/separar perguntas do curador — blocos adaptativos da
  `question-orchestration`). Permissions: remover `curador-produto-editor`
  e `val-harness`; corrigir indentação do frontmatter (linha 25). Alvo
  ≤380 linhas.
  **Acceptance criteria**:
  - [ ] Sem Modo Debug, sem DevFlowNotes
  - [ ] Fases 3 e 5 com revisão solo do rev + fluxo de repasse de achados
  - [ ] Evidências validadas por `curador-produto`
  - [ ] Gate da D13 na VALIDAÇÃO documentado (trabalho de curadoria pelas fases de dev)
  - [ ] Mediação do trabalho de curadoria explícita (blocos de perguntas)
  - [ ] permissions atualizadas e frontmatter válido
  - [ ] ≤380 linhas
  **Verification**: `.venv/bin/pytest tests/agents/test_devflow.py` (adaptado) passa
  **Dependencies**: Tasks 2, 5
  **Files**: `agents/devflow.md`
  **Estimated scope**: M

- [ ] **Task 8: Reescrever `docs/workflow-agentes-dev.md`**
  **Description**: refletir: sem comitês (fases 3/5), rev solo com skills,
  fluxo de achados (rev → devflow → especialista → nova revisão), committer
  único (D2), evidências validadas pelo curador-produto (D8), sem modo
  debug, e o schema do arquivo de planejamento (D10): seções obrigatórias
  `Status` (valores), `Regras de Produto`, `Evidências de Harness — <fase>`,
  `Perguntas`, com ordem e formato. NOVA seção "Trabalho de curadoria"
  (D13): como as fases de dev se aplicam aos artefatos de produto —
  planejamento item a item com aprovação humana via mediação devflow;
  construção com curador escrevendo docs/spec e eng-software implementando
  scripts de harness com TDD; ao final eng-software roda os harness e o
  curador verifica o verde. Alvo ≤650 linhas (hoje 931).
  **Acceptance criteria**:
  - [ ] Fases 3/5 sem comitê; fluxo de achados documentado
  - [ ] Schema do planning file formalizado com seções e formato
  - [ ] Seção "Trabalho de curadoria" completa (gate fase 1 + fases aplicadas)
  - [ ] Sem referências a editor/val-harness/modo debug
  - [ ] ≤650 linhas
  **Verification**: grep sem `val-harness|curador-produto-editor|DevFlowNotes`; teste de consistência (Task 10) passa
  **Dependencies**: Tasks 2, 7
  **Files**: `docs/workflow-agentes-dev.md`
  **Estimated scope**: L

- [ ] **Task 9: Extinguir `docs/workflow-curadoria.md` e atualizar `workflow-definicao-escopo.md`**
  **Description**: remover `docs/workflow-curadoria.md` via `git rm`
  (orquestração vira as fases de dev + seção "Trabalho de curadoria" da
  Task 8). Migrar conhecimento antes de remover: filosofia já vive em
  `agents/references/principios-documentacao.md` (completar se faltar
  trecho); template do docs/README.md e interface de harness → prompt do
  curador ou `agents/references/`; catálogo de sugestões → já é a skill
  `harness-catalog` (verificar cobertura). Atualizar
  `docs/workflow-definicao-escopo.md`: referências editor →
  curador-produto, remover menção a Modo Debug (linhas 41–44) e
  curador-produto-editor (linha 118), sequência coerente com D13
  (curadoria conduzida pelo workflow dev).
  **Acceptance criteria**:
  - [ ] `docs/workflow-curadoria.md` removido via `git rm`
  - [ ] Conhecimento migrado (filosofia, template, interface, catálogo)
  - [ ] `workflow-definicao-escopo.md` sem referências a editor/modo debug
  **Verification**: `grep -rn "workflow-curadoria\|curador-produto-editor\|DevFlowNotes" docs/ agents/` sem resultados
  **Dependencies**: Tasks 2, 8
  **Files**: `docs/workflow-curadoria.md`, `docs/workflow-definicao-escopo.md`, `agents/references/`
  **Estimated scope**: M

### Checkpoint: CP3 — commit `docs(workflow): workflow dev sem comites; curadoria unificada`

- [ ] Workflows e agentes consistentes entre si
- [ ] `.venv/bin/pytest -m "unit or tools"` passa

### Phase 4 — Consistência, docs do repo e validação

- [ ] **Task 10: Teste de consistência workflow↔agentes↔skills (D11)**
  **Description**: teste pytest (ex.: `tests/agents/test_workflow_consistency.py`)
  que: extrai nomes de agentes de `agents/*.md`; verifica se cada agente
  citado em `docs/workflow-*.md` existe; verifica se cada skill citada em
  `agents/*.md` e `docs/workflow-*.md` existe em `skills/`; e se cada
  agente com `task: allow` nas permissions aponta para agente existente.
  **Acceptance criteria**:
  - [ ] Teste detecta agente fantasma, skill inexistente e permission órfã
  - [ ] Teste passa no estado final do repo
  **Verification**: `.venv/bin/pytest tests/agents/test_workflow_consistency.py`
  **Dependencies**: Tasks 7-9
  **Files**: `tests/agents/test_workflow_consistency.py`
  **Estimated scope**: M

- [ ] **Task 11: Atualizar `README.md` e `AGENTS.md` do repo (D12)**
  **Description**: atualizar seções que citam agentes removidos ou o
  workflow antigo; manter regra de sincronização apontando para o novo
  teste de consistência.
  **Acceptance criteria**:
  - [ ] `grep -rn "curador-produto-editor\|val-harness" README.md AGENTS.md docs/ agents/` sem resultados
  - [ ] README reflete a lista final de 12 agentes
  **Verification**: grep + revisão humana
  **Dependencies**: Tasks 7-9
  **Files**: `README.md`, `AGENTS.md`
  **Estimated scope**: S

- [ ] **Task 12: Validação final**
  **Description**: rodar a suíte completa no WSL e revisar difs de todos os
  checkpoints; conferir contagem de agentes (12) e ausência de referências
  órfãs.
  **Acceptance criteria**:
  - [ ] `.venv/bin/pytest -m "unit or tools or opencode"` verde
  - [ ] Inventário de agentes: 12 arquivos em `agents/` (mais default-artifacts/references)
  - [ ] Nenhuma referência órfã a agentes/skills removidos
  **Verification**: saída do pytest + grep final
  **Dependencies**: Tasks 10, 11
  **Files**: None (verificação)
  **Estimated scope**: S

### Checkpoint: CP4 — commit `test(agents): consistencia workflow-agentes-skills; docs atualizadas`

- [ ] Suíte completa verde
- [ ] Revisão humana final antes do merge/encerramento

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Falso negativo de domínio na revisão solo do `rev` | Medium | Âncoras explícitas (padrão 95%+ Vercel); loop de correção via especialista; skill `data-modeling` fecha o gap DBA |
| Perda de conhecimento na fusão do curador (editor tinha 465L) | Medium | Preservar template e interface de harness (prompt ou `agents/references/`); critério de aceitação explícito |
| Curador unificado inflar (>350L) e sofrer context rot | Medium | Alvo ≤350L; detalhe extenso vai para `agents/references/` com âncora |
| Setup de curadoria mediado ficar lento (hop por pergunta) | Medium | devflow usa blocos adaptativos (`question-orchestration`); decide quando juntar/separar |
| Trigger da nova skill `data-modeling` falhar | Low | Description com keywords de gatilho; âncora no `dba` e no `rev`; teste de consistência garante existência |
| Testes legados referenciando agentes removidos | Low | Task 3 dedicada; suíte completa no CP final |
| Revisor `rev` tentar corrigir em vez de reportar | Medium | Regra read-only como inviolável; `devflow` repassa achados; teste de boilerplate |

## Open Questions

- Nenhuma pendente. Modelo por fase mantido; experimentos do humano com
  modelos por etapa ficam fora do escopo deste plano (usufruirão do
  mecanismo existente).
