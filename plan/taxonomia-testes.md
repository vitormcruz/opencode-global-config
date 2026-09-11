# Plano: Taxonomia de Testes Agnóstica de SO e Harness

## Overview

Reorganizar os markers de teste do repo em quatro categorias independentes de
SO e de harness, com degradação declarada por teste quando o ambiente não
permite a execução. Motivação: os markers `opencode`/`copilot` misturavam
eixos (harness e SO) e viraram proxy de plataforma; com os adapters
multiplataforma (ADR-0004), a taxonomia precisa refletir premissas reais.

## Architecture Decisions

- **D1 — Taxonomia de 4 markers, sem harness no vocabulário:**
  `unit` (sem premissas externas), `integration` (qualquer premissa externa:
  ferramenta no PATH, binário de harness, capacidade do SO), `agent_eval`
  (avaliação de agente com modelo local llama-server+Qwen, ex-`opencode` de
  integração), `all` (atalho = `unit` + `integration`, nunca inclui
  `agent_eval`). Markers `tools`, `opencode` e `copilot` deixam de existir.
- **D2 — Requisito de ambiente declarado no próprio teste:** testes que exigem
  capacidade de SO (hoje: symlink) declaram a restrição em si mesmos
  (`skipif` de plataforma com reason claro); a suíte não os executa onde não
  se aplicam e o relatório mostra o que não rodou e por quê. Mecanismo
  simétrico (aplicável a testes exclusivos de Windows no futuro). Nenhum hook
  escondido alterando a seleção pedida.
- **D3 — Regra do agente intacta:** o AGENTS.md continua exigindo que o
  agente rode sempre a suíte completa; nenhuma redação pode sugerir que o
  agente pode dispensar teste porque a suíte trata inaplicabilidade de SO. O
  `skipif` é mecanismo da suíte declarado no teste, não uma licença do agente.
- **D4 — Sem wrapper de execução:** comando único (`repo-test`) dispensado.
  Comandos crus documentados: `-m unit`, `-m integration`, `-m all`,
  `-m agent_eval`.
- **D5 — Registro:** ADR-0005 com a taxonomia; README.md e AGENTS.md com os
  comandos novos. ADRs históricos (0001-0004) permanecem como registro.
- **D6 — Pendência fora deste escopo:** investigar por que as skills de
  comunicação (humanizer-br) não foram carregadas no início de sessões
  recentes (falha do agente vs. mecanismo de ativação).

## Task List

Estado inicial: 508 unit, 37 tools (6 arquivos), 45 opencode (9 arquivos,
incluindo `tests/scripts/bootstrap_repo/test_repo_state.py` que é teste de
bootstrap, não de agente), 1 arquivo com suíte copilot
(`tests/integration/test_copilot_cli.py`), 17 testes com symlink real hoje
marcados `opencode` (15 reclassificados na execução anterior + 2
pré-existentes: `tests/bootstrap/test_installers.py` e
`tests/cli/test_svgtoimage.py`). Marker utilitário `opencode_context`
presente em fixtures da integração.

### Fase 1 — Infraestrutura de markers

- [ ] Task 1: Registrar markers novos e alias `all`
  - Description: em `pyproject.toml`, registrar `integration`, `agent_eval`,
    `all` (e renomear `opencode_context` para o vocabulário novo, mantendo as
    fixtures funcionando); remover `tools`, `opencode`, `copilot` do registro.
    Implementar o alias `all` no `conftest.py` raiz: antes da seleção,
    traduzir `all` para `unit or integration` (tradução documentada de
    atalho; não altera seleção além do que o usuário pediu; nada de exclusões
    escondidas).
  - Acceptance criteria:
    - [ ] `.venv/bin/pytest -m all --collect-only -q` seleciona exatamente a
          união de `-m unit` e `-m integration` (teste automatizado com
          subprocess compara as contagens).
    - [ ] `-m all` não inclui testes `agent_eval`.
    - [ ] Comando desconhecido em `-m` continua com erro do pytest.
  - Verification: `.venv/bin/pytest tests/ -m all --collect-only -q` e teste
    novo do alias.
  - Dependencies: None
  - Files likely touched: `pyproject.toml`, `tests/conftest.py`,
    `tests/test_taxonomy.py` (novo).
  - Estimated scope: Small
- [ ] Task 2: Migrar markers para a taxonomia nova
  - Description: `tools` → `integration` (37 testes, 6 arquivos); suíte
    `copilot` → `integration`; `opencode` → `agent_eval` nos módulos de
    integração de agente; `tests/scripts/bootstrap_repo/test_repo_state.py`:
    `opencode` → `integration` (é teste de bootstrap/CLI). Ajustar fixtures e
    `pytestmark` correspondentes (incluindo o antigo `opencode_context`).
  - Acceptance criteria:
    - [ ] Nenhum teste marcado `tools`, `opencode` ou `copilot` restante
          (grep em tests/ limpo).
    - [ ] `.venv/bin/pytest -m unit` verde; `.venv/bin/pytest -m integration`
          verde no WSL; `.venv/bin/pytest -m agent_eval --collect-only -q`
          lista os testes de avaliação de agente.
  - Verification: `.venv/bin/pytest -m "unit or integration"` verde no WSL.
  - Dependencies: Task 1
  - Files likely touched: 6 arquivos tools + `tests/integration/` +
    `tests/scripts/bootstrap_repo/test_repo_state.py` + fixtures.
  - Estimated scope: Medium
- [ ] Task 3: Requisito de SO declarado nos testes de symlink
  - Description: os 17 testes com symlink real (15 marcados `opencode` na
    rodada anterior + `tests/bootstrap/test_installers.py` e
    `tests/cli/test_svgtoimage.py`) passam a `integration` com
    `skipif` de plataforma (reason "exige symlink (POSIX)"). Sem hook, sem
    seleção mágica.
  - Acceptance criteria:
    - [ ] No WSL, os 17 rodam e passam dentro de `-m integration`.
    - [ ] `skipif` presente e com reason claro; nenhum outro mecanismo de
          exclusão.
    - [ ] `.venv/bin/pytest -m integration` no WSL não relata skip dos 17.
  - Verification: `.venv/bin/pytest -m integration` verde; inspeção dos
    decorators.
  - Dependencies: Task 2
  - Files likely touched: `tests/harnesses/test_opencode.py`,
    `tests/adapters/test_opencode_adapter.py`, `tests/lib/test_lib_sync.py`,
    `tests/bootstrap/test_installers.py`, `tests/cli/test_svgtoimage.py`.
  - Estimated scope: Small

### Checkpoint: Fase 1

- [ ] `.venv/bin/pytest -m unit` e `-m integration` verdes no WSL.
- [ ] Commit `test(pytest): taxonomia unit/integration/agent_eval com alias all`.

### Fase 2 — Registro e documentação

- [ ] Task 4: ADR-0005 + docs com a redação da regra do agente preservada
  - Description: criar `docs/adr/0005-taxonomia-testes.md` autocontida
    (contexto, decisões da taxonomia, revogação dos markers antigos, mecanismo
    de requisito de SO, fronteira suíte/agente). Atualizar README.md e
    AGENTS.md: comandos novos (`-m unit`, `-m integration`, `-m all`,
    `-m agent_eval`), seção de testes, e manter a regra do agente de rodar
    sempre a suíte completa, com redação explícita de que a inaplicabilidade
    de SO é tratada pela suíte (skipif declarado no teste) e NÃO autoriza o
    agente a deixar de rodar teste. ADRs 0001-0004 permanecem inalterados
    (registro histórico); atualizar apenas menções operacionais em
    README/AGENTS.
  - Acceptance criteria:
    - [ ] ADR-0005 não cita códigos de decisão deste plano.
    - [ ] README e AGENTS.md sem menção operacional a `-m opencode`,
          `-m copilot` ou `-m tools` (grep limpo fora de docs/adr).
    - [ ] AGENTS.md preserva a regra "nenhum skip pelo agente" com a fronteira
          suíte/agente explícita.
  - Verification: grep de `-m opencode|-m copilot|-m tools` em README.md,
    AGENTS.md, scripts/, docs/ (fora docs/adr) sem ocorrências operacionais.
  - Dependencies: Task 3
  - Files likely touched: `docs/adr/0005-taxonomia-testes.md` (novo),
    `README.md`, `AGENTS.md`.
  - Estimated scope: Medium
- [ ] Task 5: Verificação final no WSL e registro
  - Description: rodar `-m unit`, `-m integration`, `-m all` e `-m
    agent_eval` (demorado; se Docker/llama-server indisponíveis, reportar
    bloqueio, não silenciar); anotar resultados no plano; marcar checkboxes.
  - Acceptance criteria:
    - [ ] Os 4 comandos verdes no WSL (ou bloqueio reportado para agent_eval).
    - [ ] Plano atualizado com resultados.
  - Verification: saídas anotadas nesta seção.
  - Dependencies: Task 4
  - Files likely touched: `plan/taxonomia-testes.md`.
  - Estimated scope: Small

### Checkpoint: Fase 2 (final)

- [ ] Commit `docs(adr): taxonomia de testes agnostica de SO e harness`.
- [ ] Plano marcado executado; revisão independente a seguir.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Fixture `opencode_context` usada por integração quebra na renomeação | Med | Task 2 renomeia junto com os `pytestmark`; grep de uso antes de editar |
| Menções a markers antigos em scripts/skills além do previsto | Med | Task 4 varre repo inteiro (fora docs/adr e plan/) e corrige |
| Alias `all` confundido com mecanismo de exclusão escondida | Baixo | ADR-0005 e README documentam o alias como tradução literal de atalho |
| Redação das docs abrir brecha para o agente pular teste | Alto | Task 4 tem AC específico; revisor confere a redação literal |

## Open Questions

- D6 (skills de comunicação não acionadas): investigar em escopo próprio.
- Execução da suíte Windows (`-m integration` no Windows): pendente da
  validação Windows da task 10 do plano anterior (mesma máquina, mesma
  pendência).
