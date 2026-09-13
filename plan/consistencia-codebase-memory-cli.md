# Implementation Plan: Consistência do uso do codebase-memory CLI

## Overview

Aumentar a consistência com que os agentes usam o codebase-memory CLI para
descoberta de código em vez de cair em grep/glob, nos dois harnesses
(OpenCode e Copilot CLI), mantendo o modo CLI (MCP adiado; ver
`plan/mcp-codebase-memory-postergado.md`). Sintomas observados: o agente
desvia para grep/glob ignorando a regra CLI-first, e erra o comando (nome do
projeto, JSON, parâmetros). Estratégia aprovada: reforço de gatilhos com
contrato novo por detecção global (list_projects no passo 0, em vez de
indicação no AGENTS.md de cada repo), didática anti-erro na skill, e medição
agent_eval antes/depois.

## Architecture Decisions

- **D1 — Contrato por detecção global**: a skill `code-explorer-priority`
  deixa de exigir que o AGENTS.md do repositório indique codebase-memory. O
  passo 0 vira detecção: rodar `list_projects` e verificar se o repo atual
  está indexado; se sim, CLI-first; se não, grep/glob normalmente. Em repos
  não indexados o custo é um comando extra antes do grep. Justificativa:
  eliminar a necessidade de configurar cada repo novo.
- **D2 — Regra global no AGENTS.base.md**: a regra de descoberta passa a
  constar no `harness-conf/AGENTS.base.md` (propagado pelo adapter para
  todos os ambientes e repos): "repo indexado no codebase-memory =>
  descoberta de código CLI-first antes de grep/glob". O bloco gerenciado pelo
  próprio CBM no AGENTS.md global permanece intocado.
- **D3 — Didática anti-erro na skill** (sem wrapper): bloco de receita com:
  sempre `list_projects` primeiro para o nome exato do projeto; templates
  prontos para copiar (search_graph com `name_pattern`, trace_path com
  `direction`, query_graph com `query` Cypher, search_code com `pattern`);
  regras de aspas; parâmetro certo por tool.
- **D4 — Medição agent_eval antes/depois**: novo teste `agent_eval`
  (fixture `isolated_opencode` existente em `tests/integration/`) com prompts
  de descoberta real; baseline registrado antes das mudanças; mesmo teste é o
  critério de aceite depois. Requer Docker + llama-server local (Qwen3-0.6B).
- **D5 — Escopo descartado**: wrapper de invocação (scripts curtos) e
  checagem pós-hoc pelo revisor não entram neste ciclo.

## Task List

### Phase 1: Baseline

#### Task 1: Teste agent_eval de aderência e baseline

**Description:** criar teste agent_eval que envia prompts de descoberta de
código a uma sessão OpenCode real (fixture `isolated_opencode`) e verifica se
a resposta indica uso/menção do codebase-memory (ex.: menciona
`codebase-memory`, `search_graph`, `trace_path`) em vez de partir direto
para grep. Estudar antes a fixture e os testes existentes em
`tests/integration/test_skills_activation.py` para seguir o padrão. Rodar
ANTES das mudanças e registrar o baseline (espera-se adesão parcial ou
falha; registrar a saída observada no resultado).

**Acceptance criteria:**
- [ ] Teste agent_eval novo em `tests/integration/` com marker
      `agent_eval` e `agent_eval_context`, seguindo o padrão da fixture
- [ ] Baseline executado e registrado (saídas observadas, taxa de adesão)
- [ ] Sem `skip`: pré-requisito ausente vira `pytest.fail` com mensagem
      acionável (padrão do repo)

**Verification:**
- [ ] `.venv/bin/pytest -m agent_eval tests/integration/<novo_teste> -v`
      (requer Docker + llama-server; se indisponível, registrar bloqueio)

**Dependencies:** None

**Files likely touched:**
- `tests/integration/test_codebase_memory_adherence.py` (novo)

**Estimated scope:** Small

### Phase 2: Reforço de gatilhos

#### Task 2: Skill com contrato novo e receita anti-erro

**Description:** reescrever `harness-conf/skills/code-explorer-priority/SKILL.md`
para o contrato por detecção (D1) e incluir a receita anti-erro (D3):
description com triggers de descoberta (busca, onde fica, quem chama, como
funciona...) e instrução de detecção; corpo com passo 0 = `list_projects`
com decisão indexado/não-indexado, templates prontos por tool, parâmetros
certos e regras de aspas. Atualizar `tests/skills/test_code_explorer.py`
(contrato novo: strings, seções, `CLI_COMMANDS`).

**Acceptance criteria:**
- [ ] Description sem "APENAS quando o AGENTS.md indicar"; com detecção e
      triggers de descoberta
- [ ] Passo 0 por detecção (`list_projects`) com caminho para repo não
      indexado (grep/glob)
- [ ] Receita anti-erro com templates por tool e parâmetros corretos
- [ ] `tests/skills/test_code_explorer.py` atualizado e verde

**Verification:**
- [ ] `.venv/bin/pytest tests/skills/test_code_explorer.py -v`

**Dependencies:** Task 1 (baseline registrado antes das mudanças)

**Files likely touched:**
- `harness-conf/skills/code-explorer-priority/SKILL.md`
- `tests/skills/test_code_explorer.py`

**Estimated scope:** Medium

#### Task 3: Regra global no AGENTS.base.md e revisão do command

**Description:** adicionar a `harness-conf/AGENTS.base.md` a regra condicional
de descoberta (D2): quando o repo estiver indexado no codebase-memory,
descoberta de código CLI-first antes de grep/glob, com remissão à skill
`code-explorer-priority`. Revisar `harness-conf/commands/index-codebase.md`:
Etapa 3 (verificação de instruções no AGENTS.md do repo) ajustada ao
contrato novo (a indicação por repo não é mais requisito; verificar apenas
consistência opcional). Verificar testes de boilerplate/estrutura que fixam
conteúdos desses arquivos e atualizá-los conforme o novo contrato.

**Acceptance criteria:**
- [ ] `AGENTS.base.md` com a regra condicional (curta; detalhes ficam na
      skill, sem listar tools no base, preservando
      `test_repo_structure.py:367`)
- [ ] `index-codebase.md` coerente com o contrato por detecção
- [ ] Testes afetados atualizados e verdes

**Verification:**
- [ ] `.venv/bin/pytest tests/scripts/bootstrap_repo/test_repo_structure.py
      tests/agents/ -v`

**Dependencies:** Task 2 (mesmo contrato)

**Files likely touched:**
- `harness-conf/AGENTS.base.md`
- `harness-conf/commands/index-codebase.md`
- `tests/scripts/bootstrap_repo/test_repo_structure.py`
- `tests/harnesses/` (se o adapter propagar validações)

**Estimated scope:** Medium

### Checkpoint: Fase 2 concluída
- [ ] Suíte completa `.venv/bin/pytest -m all` verde
- [ ] Commits em unidades lógicas: skill+testes (docs(skill)), base+command
      (docs(agents))

### Phase 3: Re-avaliação

#### Task 4: agent_eval pós-mudança e registro antes/depois

**Description:** rodar o teste agent_eval da Task 1 após as mudanças e
comparar com o baseline: adesão deve subir (critério de aceite: teste
passa onde o baseline falhava, ou adesão registrada melhora). Registrar a
comparação no resultado para o humano.

**Acceptance criteria:**
- [ ] agent_eval pós-mudança aprovado
- [ ] Comparação antes/depois registrada no resultado do executor

**Verification:**
- [ ] `.venv/bin/pytest -m agent_eval -v`
- [ ] Suíte completa final `.venv/bin/pytest -m all`

**Dependencies:** Fase 2 concluída

**Files likely touched:**
- Nenhum (medição)

**Estimated scope:** Small

### Checkpoint: Conclusão
- [ ] Revisão independente do revisor aprovando o ciclo
- [ ] Registrar antes/depois no plano e concluir

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Skill ativa em repo não indexado (comando extra) | Baixo | Passo 0 explícito com queda rápida para grep/glob |
| Testes antigos fixam o contrato velho | Médio | Tasks 2-3 listam os arquivos de teste; atualizar junto |
| agent_eval exige Docker + llama-server | Médio | Registrar bloqueio e pytest.fail com mensagem acionável; reexecutar quando disponível |
| Qwen3-0.6B pequeno demais para medir aderência | Médio | Prompts diretos; se ainda inconclusivo, registrar como limitação e usar a suíte unit/integration como aceite |
| AGENTS.base.md inflado (regra global verbosa) | Baixo | Regra curta e condicional; detalhes na skill |

## Open Questions

Nenhuma pendente. Decisões D1-D5 aprovadas pelo humano.
