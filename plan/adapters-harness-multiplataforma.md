# Plano: Adapters de Harness Multiplataforma

## Overview

Remover o acoplamento SO→harness: hoje Linux/WSL configura somente o OpenCode
e Windows somente o Copilot CLI (ADR-0001 AD-5/AD-6, bloqueio em
`adapters/opencode.py` e seleção por SO em `bootstrap/main.py`). O novo
comportamento: o bootstrap detecta o SO corrente e adapta **todos os harnesses
instalados** naquele SO, com estratégia de materialização por ambiente. A
arquitetura vira um registry extensível de harnesses, facilitando adicionar
novos clientes no futuro.

## Architecture Decisions

- **D1 — Windows usa cópia sincronizada.** A config global materializada no
  Windows é sempre cópia sincronizada a cada execução (modelo do adapter
  Copilot atual), sem symlink/junction. Evita dependência de Developer Mode e
  privilégios; contrapartida: divergência possível até o próximo sync.
- **D2 — Default: todos os harnesses instalados.** O bootstrap detecta quais
  harnesses estão instalados no SO corrente e configura todos; ausentes são
  ignorados com aviso. Flag `--harness` restringe a subconjunto.
- **D3 — Escopo: arquitetura completa.** Registry central + contrato comum de
  harness + migração dos dois adapters existentes + ADR novo revogando AD-5/AD-6
  do ADR-0001 + testes multi-SO. Não apenas remoção de bloqueios.
- **D4 — Env vars no Windows via HKCU\Environment.** No Windows nativo, o
  adapter OpenCode persiste `OPENCODE_ENABLE_EXA` (e demais env vars de
  usuário) em `HKEY_CURRENT_USER\Environment` via `winreg`, com broadcast de
  `WM_SETTINGCHANGE` (ctypes) para o Explorer recarregar o ambiente sem
  logoff. A persistência existente do PATH (installers/core.py) também passa a
  broadcastar.
- **D5 — Copilot instalável pelo bootstrap em Linux/WSL.** A dependência
  `copilot` do registry passa a ter `supported_environments` com Linux/WSL
  além de Windows, com install method via npm (`npm install --global --prefix
  ~/.local @github/copilot`). Provisionamento de máquina nova fica sem passos
  manuais.
- **D6 — Testes de integração permanecem por SO atual.** `-m opencode`
  continua WSL/Linux (Docker + llama-server); `-m copilot` continua Windows.
  O que vira multi-SO nesta mudança são os testes unitários/tools dos
  adapters e do registry. Execução cruzada das integrações fica registrada
  como open question futura.
- **D7 — Arquitetura: factory injeta strategy por SO; adapter cego ao SO.**
  Contrato `HarnessAdapter` por harness (OpenCode, Copilot) consumido pelo
  bootstrap via registry. Cada harness que varia por SO tem interface de
  strategy própria (ex.: `OpenCodeEnvStrategy`) com implementações
  `OpenCodePosix` (symlink + `.bashrc`) e `OpenCodeWindows` (cópia
  sincronizada + HKCU\Environment). Factory com mapa `strategy[env]`
  instancia o adapter já com a strategy correta (injeção no construtor);
  o adapter não contém decisão de SO. Copilot hoje não varia por SO e não
  ganha strategy. Reuso entre harnesses via utilitários de `lib/`
  (cópia sincronizada, backup), não hierarquia genérica. Entry points
  `opencode-adapter` e `opencode-copilot-adapter` permanecem como wrappers
  finos sobre os adapters.

## Task List

Estado inicial relevante:

- Bloqueio SO→harness: `src/opencode_config/adapters/opencode.py:350`
  (levanta `UnsupportedEnvironmentError` no Windows) e
  `src/opencode_config/bootstrap/main.py:275-282` (escolhe adapter por SO).
- Teste que precisa inverter: `tests/adapters/test_opencode_adapter.py:272`
  (afirma que WINDOWS levanta erro).
- Env vars hoje: `.bashrc` via `_setup_bashrc` em `adapters/opencode.py`;
  PATH do usuário no Windows via `winreg` em
  `bootstrap/installers/core.py:106` (sem broadcast).
- Cópia sincronizada reutilizável já existe dentro de
  `adapters/copilot.py` (`_copy_path`, `_remove_path`, `_backup_if_exists`).
- Dependência `copilot` Windows-only: `bootstrap/registry.py:353-368`.
- Env var de escape por harness: `OPENCODE_SKIP_OPENCODE_ADAPTER` e
  `OPENCODE_SKIP_COPILOT_ADAPTER` (usadas em `tests/test_crawl4ai_cleanup.py`
  e `tests/scripts/bootstrap_repo/test_repo_state.py`).

Layout de código decidido:

- `src/opencode_config/harnesses/` — módulo novo: `__init__.py` (contrato
  `HarnessAdapter` + registry `HARNESSES`), `factory.py` (`criarAdapters`,
  mapa `strategy[env]`), `opencode.py` (`OpenCodeAdapter` +
  `OpenCodeEnvStrategy` + `OpenCodePosix` + `OpenCodeWindows`),
  `copilot.py` (`CopilotAdapter`).
- `src/opencode_config/adapters/{opencode,copilot}.py` — viram wrappers
  finos dos entrypoints (pyproject continua apontando para eles).
- `src/opencode_config/lib/` — utilitários compartilhados: `sync.py`
  (cópia sincronizada, backup, symlink seguro) e `windows_env.py`
  (winreg + broadcast `WM_SETTINGCHANGE`).
- Testes espelham: `tests/harnesses/`, `tests/lib/`.

### Fase 1 — Fundação

- [ ] Task 1: Extrair utilitários de sincronização para `lib/sync.py`
  - Description: mover `_backup_if_exists`, `_copy_path`, `_remove_path`,
    cópia idempotente de diretórios e criação de symlink (com verificação de
    destino já correto) de `adapters/copilot.py` e `adapters/opencode.py`
    para `lib/sync.py`, como funções puras. Os dois adapters passam a
    chamar os utilitários; nenhum comportamento muda.
  - Acceptance criteria:
    - [ ] `lib/sync.py` expõe backup, cópia sincronizada (arquivo e
          árvore, apagando extras), remoção e link com os contratos atuais.
    - [ ] `opencode-adapter` e `opencode-copilot-adapter` produzem os
          mesmos destinos de antes (diff vazio num diretório de teste).
    - [ ] `tests/lib/test_sync.py` cobre backup de arquivo existente,
          idempotência da cópia e link já-apontando-pra-fonte.
  - Verification: `.venv/bin/pytest tests/lib/test_sync.py
    tests/adapters -m "unit or tools"` verde no WSL.
  - Dependencies: None
  - Files likely touched: `src/opencode_config/lib/sync.py` (novo),
    `src/opencode_config/adapters/opencode.py`,
    `src/opencode_config/adapters/copilot.py`,
    `tests/lib/test_sync.py` (novo).
  - Estimated scope: Medium
- [ ] Task 2: Contrato `HarnessAdapter` + registry + factory com mapa
  - Description: criar `harnesses/__init__.py` com o contrato (name,
    installed(env), apply(repo, opts)) e a lista `HARNESSES`; criar
    `harnesses/factory.py` com `criar_adapters(env, selecao)` que instancia
    cada adapter passando a strategy pelo mapa `STRATEGY[env]` (injeção no
    construtor; adapters não conhecem SO). Por enquanto a factory só
    enxerga fakes/stubs — os adapters reais entram nas fases seguintes.
  - Acceptance criteria:
    - [ ] Factory filtra por seleção (`--harness`) e injeta a strategy
          certa por ambiente (LINUX/WSL→Posix, WINDOWS→Windows) usando o
          mapa, sem `if` espalhado.
    - [ ] Adapter fake de teste não recebe `env` nem escolhe strategy.
    - [ ] `tests/harnesses/test_factory.py` cobre os 3 ambientes e a
          seleção por nomes.
  - Verification: `.venv/bin/pytest tests/harnesses -m unit` verde.
  - Dependencies: None
  - Files likely touched: `src/opencode_config/harnesses/__init__.py`
    (novo), `src/opencode_config/harnesses/factory.py` (novo),
    `tests/harnesses/test_factory.py` (novo).
  - Estimated scope: Medium

### Checkpoint: Fase 1

- [ ] `.venv/bin/pytest -m "unit or tools"` verde no WSL.
- [ ] Commit `refactor(harnesses): extrair sync para lib e criar factory`
      (tasks 1-2).

### Fase 2 — OpenCode multi-SO

- [ ] Task 3: `OpenCodePosix` + `OpenCodeAdapter` consumindo strategy
  - Description: mover a lógica atual de `adapters/opencode.py`
    (symlinks dos 4 destinos, `_sync_agents_base`, `_setup_bashrc`,
    plano/confirmação/backup) para `harnesses/opencode.py`, separando o que
    é do adapter (fluxo, AGENTS.md, backup, confirmação) do que é da
    strategy POSIX (`config_dir`, materialize com symlink, setup_env no
    `.bashrc`). `adapters/opencode.py` vira wrapper do entrypoint
    chamando `OpenCodeAdapter` com `OpenCodePosix`. O bloqueio de Windows
    (linhas 350-361) sai deste módulo — a recusa por SO passa a não
    existir no adapter.
  - Acceptance criteria:
    - [ ] `opencode-adapter --yes` no WSL produz exatamente os mesmos
          links/AGENTS.md/.bashrc de antes (comparar com estado pré-task).
    - [ ] `OpenCodeAdapter` não referencia `EnvironmentKind` nem escolhe
          strategy; recebe no construtor.
    - [ ] Testes de `tests/adapters/test_opencode_adapter.py` migrados
          para `tests/harnesses/test_opencode.py` e verdes (exceto o caso
          Windows-lança-erro, que a Task 4 inverte).
  - Verification: `.venv/bin/pytest tests/harnesses -m unit` verde;
    smoke manual `opencode-adapter --yes` com HOME temporário.
  - Dependencies: Task 1, Task 2
  - Files likely touched: `src/opencode_config/harnesses/opencode.py`
    (novo), `src/opencode_config/harnesses/factory.py`,
    `src/opencode_config/adapters/opencode.py`,
    `tests/harnesses/test_opencode.py` (novo, migração).
  - Estimated scope: Large (migração de módulo; dividir em dois commits
    se passar de ~300 linhas: extração strategy / wrapper)
- [ ] Task 4: `OpenCodeWindows` (cópia + HKCU + broadcast)
  - Description: implementar a strategy Windows em `harnesses/opencode.py`:
    `config_dir` = `Path.home()/".config"/"opencode"` (home do Windows),
    `materialize` = cópia sincronizada dos 4 destinos via `lib/sync.py`
    (agentes/skills/commands/opencode.json), `setup_env` = gravar
    `OPENCODE_ENABLE_EXA` em HKCU\Environment via `lib/windows_env.py` e
    broadcastar. Registrar no mapa da factory (WINDOWS→OpenCodeWindows).
    Inverter o teste de recusa: agora Windows configura com cópia.
  - Acceptance criteria:
    - [ ] Mapa da factory retorna `OpenCodeWindows` para WINDOWS e
          `OpenCodePosix` para LINUX/WSL.
    - [ ] `setup_env` grava a variável e broadcasta; a gravação usa
          `winreg` importado de forma lazy (módulo importável no Linux).
    - [ ] Teste unitário com fake de registro valida valor gravado e
          chamada de broadcast, sem tocar no registro real.
    - [ ] Teste antigo `WINDOWS levanta erro` substituído por
          `WINDOWS materializa com cópia` (verificando destinos em
          diretório temporário como home).
  - Verification: `.venv/bin/pytest tests/harnesses -m unit` verde no
    WSL; no Windows `.\.venv\Scripts\pytest.exe tests/harnesses -m unit`.
  - Dependencies: Task 3
  - Files likely touched: `src/opencode_config/harnesses/opencode.py`,
    `src/opencode_config/harnesses/factory.py`,
    `src/opencode_config/lib/windows_env.py` (novo),
    `tests/harnesses/test_opencode.py`, `tests/lib/test_windows_env.py`
    (novo).
  - Estimated scope: Medium
- [ ] Task 5: Broadcast na persistência existente do PATH
  - Description: `_persist_windows_user_path` (installers/core.py) passa a
    broadcastar `WM_SETTINGCHANGE` via `lib/windows_env.py` após gravar.
  - Acceptance criteria:
    - [ ] Persistência do PATH reusa a mesma função de broadcast da
          lib (sem duplicar ctypes).
    - [ ] Teste unit com monkeypatch confirma broadcast após gravação.
  - Verification: `.venv/bin/pytest tests/bootstrap tests/lib -m unit`.
  - Dependencies: Task 4 (usa `lib/windows_env.py`)
  - Files likely touched:
    `src/opencode_config/bootstrap/installers/core.py`,
    `tests/bootstrap/test_installers.py`, `tests/lib/test_windows_env.py`.
  - Estimated scope: Small

### Checkpoint: Fase 2

- [ ] `.venv/bin/pytest -m "unit or tools"` verde no WSL.
- [ ] `.venv/bin/pytest -m opencode` verde no WSL (integração OpenCode
      inalterada).
- [ ] Commit `feat(harnesses): opencode adapter multi-SO com strategy`
      (tasks 3-5).

### Fase 3 — Copilot no registry + bootstrap multi-harness

- [ ] Task 6: `CopilotAdapter` implementando o contrato
  - Description: envolver o `synchronize` atual em `harnesses/copilot.py`
    como `CopilotAdapter` (name="copilot", installed via
    `shutil.which("copilot")`, apply delega ao synchronize com os mesmos
    argumentos/`--dest-root`). `adapters/copilot.py` vira wrapper.
    Registrar na factory (sem strategy — não varia por SO).
  - Acceptance criteria:
    - [ ] `opencode-copilot-adapter` comporta-se igual (21 testes atuais
          migrados/adaptados verdes em `tests/harnesses/test_copilot.py`).
    - [ ] Factory retorna 2 adapters quando ambos selecionados.
  - Verification: `.venv/bin/pytest tests/harnesses -m unit` verde.
  - Dependencies: Task 2
  - Files likely touched: `src/opencode_config/harnesses/copilot.py`
    (novo), `src/opencode_config/harnesses/factory.py`,
    `src/opencode_config/adapters/copilot.py`,
    `tests/harnesses/test_copilot.py` (migração).
  - Estimated scope: Medium
- [ ] Task 7: Bootstrap itera sobre a factory
  - Description: `bootstrap/main.py` remove a seleção por SO (linhas
    275-283) e passa a chamar `criar_adapters(env, selecao)`; nova flag
    `--harness a,b` (default: todos); para cada adapter, `installed()`
    decide configurar ou avisar "não instalado, pulando".
    `OPENCODE_SKIP_OPENCODE_ADAPTER` e `OPENCODE_SKIP_COPILOT_ADAPTER`
    continuam pulando o harness correspondente (compat com
    test_crawl4ai_cleanup e test_repo_state).
  - Acceptance criteria:
    - [ ] No WSL com opencode+copilot instalados: `opencode-bootstrap
          --yes` configura `~/.config/opencode` e `~/.copilot` e reporta
          ambos.
    - [ ] Harness ausente no PATH: aviso e exit code não-erro.
    - [ ] `--harness copilot` configura só o Copilot.
    - [ ] `--help` documenta a flag; teste do crawl4ai_cleanup e
          test_repo_state seguem verdes sem edição (ou com edição mínima
          justificada).
  - Verification: `.venv/bin/pytest tests/bootstrap
    tests/test_crawl4ai_cleanup.py tests/scripts/bootstrap_repo
    -m "unit or tools"`; smoke manual do bootstrap no WSL.
  - Dependencies: Task 3, Task 4, Task 6
  - Files likely touched: `src/opencode_config/bootstrap/main.py`,
    `src/opencode_config/bootstrap/interactive.py` (se o help/tabela
    mencionar harnesses), `tests/bootstrap/test_entrypoints.py`.
  - Estimated scope: Medium
- [ ] Task 8: Dependência copilot instalável em Linux/WSL
  - Description: `bootstrap/registry.py` — `copilot` ganha
    `supported_environments={LINUX, WSL, WINDOWS}` com install method npm
    user-space para POSIX (`npm install --global --prefix ~/.local
    @github/copilot`), mantendo o método Windows atual.
  - Acceptance criteria:
    - [ ] `spec.install_method_for(WSL)` retorna comando npm user-space.
    - [ ] Tabela do `--check-only` exibe o copilot nos 3 ambientes.
    - [ ] Testes em `tests/bootstrap/test_detect.py` cobrem LINUX/WSL.
  - Verification: `.venv/bin/pytest tests/bootstrap -m "unit or tools"`.
  - Dependencies: None
  - Files likely touched: `src/opencode_config/bootstrap/registry.py`,
    `tests/bootstrap/test_detect.py`.
  - Estimated scope: Small

### Checkpoint: Fase 3

- [ ] `.venv/bin/pytest -m "unit or tools or opencode"` verde no WSL.
- [ ] Smoke do bootstrap configurou os dois harnesses no WSL.
- [ ] Commit `feat(bootstrap): orquestra harnesses via factory`
      (tasks 6-8).

### Fase 4 — ADR, docs e validação cruzada

- [ ] Task 9: ADR-0004 + atualização de docs
  - Description: criar `docs/adr/0004-adapters-harness-multiplataforma.md`
    (contexto, decisões D1-D7 em linguagem autocontida, consequências,
    revogação de AD-5/AD-6 do ADR-0001); adicionar nota de revogação nas
    decisões correspondentes do ADR-0001; atualizar README.md (seções de
    dependências, comandos por SO, destinos), AGENTS.md do repo (Bootstrap,
    Testes, Sincronização dos Adaptadores), `adapters/opencode/README.md`,
    `adapters/copilot-cli/README.md` e `scripts/bootstrap_repo/README.md`.
  - Acceptance criteria:
    - [ ] ADR-0004 autocontida (sem citar códigos D1-D7 do plano).
    - [ ] ADR-0001 aponta a revogação de AD-5/AD-6.
    - [ ] README/AGENTS sem menção a "exclusivo de Linux/WSL" /
          "exclusivo do Windows" fora do contexto histórico.
  - Verification: revisão textual + `grep -rn "exclusivo" README.md
    AGENTS.md adapters/ docs/adr/0001*` só em contexto histórico.
  - Dependencies: Task 7
  - Files likely touched: `docs/adr/0004-*.md` (novo),
    `docs/adr/0001-migracao-mcp-para-cli.md`, `README.md`, `AGENTS.md`,
    `adapters/opencode/README.md`, `adapters/copilot-cli/README.md`,
    `scripts/bootstrap_repo/README.md`.
  - Estimated scope: Medium
- [ ] Task 10: Validação cruzada WSL + Windows
  - Description: rodar as suítes completas nos dois ambientes e um smoke
    do bootstrap em cada um; registrar resultado no plano.
  - Acceptance criteria:
    - [ ] WSL: `.venv/bin/pytest -m "unit or tools or opencode"` verde.
    - [ ] Windows: `.\.venv\Scripts\pytest.exe -m "unit or tools or
          copilot"` verde (valida winreg/broadcast de verdade).
    - [ ] Smoke Windows: bootstrap configura OpenCode (cópia em
          `%USERPROFILE%\.config\opencode`) e Copilot.
  - Verification: resultados anotados nesta seção; achados viram correção
    ou replan.
  - Dependencies: Task 9
  - Files likely touched: nenhum (validação); correções pontuais se
    achados.
  - Estimated scope: Small

### Checkpoint: Fase 4 (final)

- [ ] Suítes verdes nos dois SOs.
- [ ] Commit `docs(adr): adapters de harness multiplataforma` (task 9).
- [ ] Plano marcado como executado e aprovado pelo revisor.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `winreg`/`ctypes` inexistentes no Linux quebram import em teste WSL | Med | Import lazy em `lib/windows_env.py`; adapters só importam no Windows; fakes injetáveis nos unit tests |
| Cópia sincronizada diverge da fonte entre syncs (D1) | Med | Bootstrap idempotente documentado como re-sync; ADR registra trade-off |
| Migração do adapter OpenCode quebra integração `-m opencode` | Alto | Task 3 exige paridade de destinos; checkpoint da Fase 2 roda a suíte de integração antes de prosseguir |
| Env vars de escape (`OPENCODE_SKIP_*`) mudam de semântica | Baixo | Manter nomes atuais mapeando 1:1 para harness; testes existentes como rede |
| Home do Windows resolver errado (`HOME` setado no PowerShell) | Baixo | Usar `Path.home()` (respeita USERPROFILE) e não `os.environ["HOME"]`; teste com HOME venenoso |
| Escopo crescer para execução cruzada de integração | Med | D6 fixa fronteira; cruzamento fica em Open Questions |

## Open Questions

- Execução cruzada das integrações (suíte `-m opencode` no Windows com
  Docker Desktop; `-m copilot` no WSL): adiar para decisão própria depois
  desta mudança.
- CLI `opencode` como dependência instalável do bootstrap (hoje instalado
  separadamente, ex.: `~/.opencode/bin`): fora do escopo; avaliar depois.
- Copilot variando por SO no futuro: ganha strategy própria simétrica à do
  OpenCode quando houver variação real.

## Configuração de Execução

- **Executor:** subagente `worker`, modelo `zai-coding-plan/glm-5.3`
  (frontmatter de `harness-conf/agents/worker.md`).
- **Revisor:** subagente `revisor`, modelo `zai-coding-plan/glm-5.3`
  (frontmatter de `harness-conf/agents/revisor.md`).
- Plataforma: OpenCode (agentes nativos `worker` e `revisor`; a tool `task`
  não aceita modelo no spawn — o modelo vem do frontmatter do agente).
