# Implementation Plan: Habilitar tool `question` e regra de alternativa em perguntas

## Overview

Agentes primary que conduzem conversa com o humano (smart-planner, devflow,
analista) não têm acesso à tool `question`: o default de permissão do OpenCode
para agentes customizados é `question: "deny"` (código-fonte: `agent.ts` —
apenas `build` e `plan` nativos setam `question: "allow"`). Sem a tool, os
agentes degradam o protocolo conversacional para texto puro.

Além da habilitação, registrar na skill `question-orchestration` a regra
comportamental: toda pergunta feita ao humano deve oferecer sempre uma
alternativa de escape — responder por texto livre, dar outra informação ou pedir
mais contexto; nunca uma pergunta fechada sem saída.

Escopo: frontmatter de 3 agentes, skill local (sem upstream), teste de
consistência.

## Architecture Decisions

- **D1 (aprovada): habilitar `question: allow` via frontmatter, por agente.**
  Não usar permissão global no `opencode.json` (atingiria subagentes, onde a
  tool pendura em modo non-interactive). Editar a skill não habilita tool —
  skill é instrução, permissão é frontmatter.
- **D2 (aprovada): agentes no escopo: `smart-planner`, `devflow` e `analista`.**
  Todos `mode: primary` e conduzem conversa com o humano via
  `question-orchestration` (direto ou mediado).
- **D3 (aprovada): nova seção "Alternativa de escape obrigatória" na skill
  `question-orchestration`**, inserida entre "Perguntas em blocos adaptativos"
  e "Confirmação e continuidade de decisões", com o texto: toda pergunta ao
  humano — via tool `question` ou em texto — oferece sempre um caminho de
  escape: resposta livre por texto, opção explícita do tipo "Outro (responder
  por texto)" ou "Nenhuma das opções — quero dar mais contexto". Nunca formule
  pergunta cujas únicas saídas sejam as opções apresentadas. A UI da tool
  aceita resposta custom por padrão, mas o escape deve estar visível no
  enunciado ou nas opções — nunca pressuposto.
- **D4 (aprovada): estender `tests/agents/test_workflow_consistency.py`** com
  checagem: agente que referencia `question-orchestration` deve ter
  `question: allow` no frontmatter. Sem arquivo de teste novo.
- **D5 (aprovada): modelos por papel na execução.** Executor: `worker`
  (`opencode-go/gpt-5.6-luna`, já no frontmatter). Revisor: `revisor`
  (`zai-coding-plan/glm-5.3`, já no frontmatter). Nenhuma edição de modelo
  necessária; a tool `task` usa os frontmatters.

## Task List

### Phase 1: Habilitação e regra

- [ ] **Task 1: Adicionar `question: allow` ao frontmatter dos 3 agentes**

  **Description:** Editar o bloco `permission:` do frontmatter YAML de cada
  agente, adicionando a linha `  question: allow` (2 espaços de indentação,
  chave simples — `question` aceita só shorthand).

  - `harness-conf/agents/smart-planner.md` — inserir como primeira chave após
    `permission:` (antes de `edit:`).
  - `harness-conf/agents/devflow.md` — inserir como primeira chave após
    `permission:` (antes de `edit:`).
  - `harness-conf/agents/analista.md` — o bloco `permission:` hoje só tem
    `task:`; inserir `  question: allow` antes de `  task:`.

  Não alterar nenhuma outra linha dos arquivos.

  **Acceptance criteria:**
  - [ ] Os 3 frontmatters contêm `  question: allow` com indentação correta.
  - [ ] YAML dos frontmatters permanece válido (blocos `---` intactos).
  - [ ] Nenhuma outra linha modificada (`git diff` mostra só as 3 inserções).

  **Verification:**
  - [ ] `git diff` mostra exatamente 3 linhas adicionadas (1 por arquivo).
  - [ ] Task 3 roda verde com os frontmatters novos.

  **Dependencies:** None
  **Files likely touched:**
  - `harness-conf/agents/smart-planner.md`
  - `harness-conf/agents/devflow.md`
  - `harness-conf/agents/analista.md`
  **Estimated scope:** XS (3 arquivos, 1 linha cada)

- [ ] **Task 2: Seção "Alternativa de escape obrigatória" na skill**

  **Description:** Editar `harness-conf/skills/question-orchestration/SKILL.md`
  inserindo nova seção `## Alternativa de escape obrigatória` entre
  `## Perguntas em blocos adaptativos` e `## Confirmação e continuidade de
  decisões`, com o texto aprovado na D3. Linhas com no máximo 120 colunas.
  Não alterar nenhuma outra seção. A skill é local (sem `UPSTREAM.md`); o
  symlink global aponta para o repo, então editar o repo atualiza o global.

  Texto da seção (a produzir no arquivo, formato autocontido):

  ```
  ## Alternativa de escape obrigatória

  Toda pergunta ao humano — via tool `question` ou em texto — oferece sempre
  um caminho de escape: resposta livre por texto, opção explícita do tipo
  "Outro (responder por texto)" ou "Nenhuma das opções — quero dar mais
  contexto". Nunca formule pergunta cujas únicas saídas sejam as opções
  apresentadas. A UI da tool aceita resposta custom por padrão, mas o escape
  deve estar visível no enunciado ou nas opções — nunca pressuposto.
  ```

  **Acceptance criteria:**
  - [ ] Seção presente na posição exata (entre as duas seções citadas).
  - [ ] Texto fiel ao aprovado na D3, autocontido, sem citar este plano.
  - [ ] Nenhuma outra seção do SKILL.md alterada.
  - [ ] Linhas ≤ 120 colunas.

  **Verification:**
  - [ ] `git diff` restrito à inserção da seção.
  - [ ] Teste de skills do repositório continua verde (Task 3 / suíte unit).

  **Dependencies:** None
  **Files likely touched:**
  - `harness-conf/skills/question-orchestration/SKILL.md`
  **Estimated scope:** XS (1 arquivo)

- [ ] **Task 3: Estender teste de consistência com guarda de permissão**

  **Description:** Adicionar teste em
  `tests/agents/test_workflow_consistency.py` seguindo o padrão do arquivo
  (marker `@pytest.mark.unit`, helpers existentes `_extract_frontmatter`,
  `_read_agent_files`). Lógica: para cada agente em `harness-conf/agents/*.md`
  cujo conteúdo referencie `question-orchestration` (backtick ou tabela), o
  frontmatter deve conter linha que case com
  `^\s{2}question:\s*allow\s*$`. Falha listando agente → permissão ausente.
  Incluir também um teste sintético no estilo do existente
  `test_extract_task_allow_agents_detects_synthetic_orphan` (frontmatter
  fake sem `question: allow` → parser detecta ausência).

  **Acceptance criteria:**
  - [ ] Novo teste de inventário passa com os frontmatters pós-Task 1.
  - [ ] Teste sintético demonstra detecção de ausência da permissão.
  - [ ] Nenhum teste existente alterado ou removido.
  - [ ] Suíte `-m "unit or tools"` verde no executável do SO.

  **Verification:**
  - [ ] `.venv/bin/pytest tests/agents/test_workflow_consistency.py -m unit`
        verde (WSL/Linux).
  - [ ] Remover mentalmente/comprovadamente `question: allow` de um agente
        faz o teste falhar (provar uma vez e restaurar).

  **Dependencies:** Task 1 (frontmatters precisam existir para o teste de
  inventário passar).
  **Files likely touched:**
  - `tests/agents/test_workflow_consistency.py`
  **Estimated scope:** S (1 arquivo, novo teste + sintético)

### Checkpoint: Fase 1 completa

- [ ] Suíte `.venv/bin/pytest -m "unit or tools"` verde (WSL/Linux).
- [ ] `git diff` contém exatamente: 3 frontmatters + 1 seção de skill + testes.
- [ ] Commit local (unidade lógica única). Mensagem sugerida:
      `feat(agents): habilitar tool question nos agentes conversacionais`
      — incluir skill e teste no mesmo commit (são partes da mesma
      habilitação) ou separar `test(agents):` se o agrupamento ficar grande.
- [ ] README não é afetado (sem mudança de bootstrap/dependências).

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Upstream mudar o default de `question` ou o comportamento da tool | Médio | Teste de consistência guarda os frontmatters; revisar em upgrades do OpenCode |
| Tool `question` chamada em modo non-interactive (`opencode run`) pendura ou é negada | Baixo | Agentes do escopo são primary, uso interativo; upstream já trata deny com "best judgment" (fix #14607) |
| Modelo formula pergunta fechada mesmo com a regra na skill | Médio | Regra visível na fonte única (D3) + revisão independente ao final |
| Edição da skill propagar imediatamente via symlink global | Baixo | Comportamento desejado; sem reinstalação necessária |

## Open Questions

(nenhuma — todos os ramos resolvidos: D1–D4)
