# Implementation Plan: Atualização de libs pinadas no bootstrap

## Overview

Atualizar três dependências com versão fixa no bootstrap do repo
(codebase-memory-mcp, pandoc e PortableGit) e, sobre essa base, revisar a
arquitetura de uso das ferramentas externas: verificação de otimização do
codebase-memory (0.9 -> 0.10) e decisão multi-harness para configurar
ferramentas com MCP e fallback CLI (D4). As versões vivem em dois pontos que
precisam permanecer sincronizados: as constantes em
`src/opencode_config/bootstrap/installers/core.py` e as strings copiáveis em
`src/opencode_config/bootstrap/registry.py`. Também atualizam a tabela de
dependências do `README.md` e os testes que verificam a versão do
codebase-memory-mcp.

## Architecture Decisions

- **D1 — PortableGit 2.55.0.windows.5**: usar a última patch da série 2.55.0
  (com hotfixes de segurança). Implica mudar o formato do asset: a tag de
  download é `v2.55.0.windows.5` e o arquivo é
  `PortableGit-2.55.0.5-64-bit.7z.exe` (o `.windows.` vira `.` no nome do
  arquivo). Hoje o código assume sufixo `.windows.1` fixo e nome igual à
  versão; ambos precisam ser ajustados.
- **D2 — codebase-memory-mcp 0.10.8**: bump de 0.9.0 para a última publicada.
  Salto de minor com possível breaking change na CLI; os testes reais do
  binário (`tests/scripts/codebase-memory/test_real.py`) cobrem regressões.
  O `minimum_version=(0, 9, 0)` do registry permanece válido.
- **D3 — pandoc 3.11**: bump de 3.7.0.2 para a última release. Assets
  `pandoc-3.11-linux-amd64.tar.gz` e `pandoc-3.11-windows-x86_64.zip`
  confirmados. Sem mudança estrutural.
- **D4 — Configuração multi-harness de ferramentas externas**: as ferramentas
  usadas por skills/commands passam a seguir três níveis: (1) configuração
  genérica quando uma única forma serve todos os harnesses; (2) configuração
  específica por harness via adapter quando o genérico não basta (mesmo padrão
  dos adapters OpenCode/Copilot); (3) fallback garantido: como MCP pode não
  estar disponível dependendo da instalação, toda ferramenta com modo MCP
  mantém caminho CLI documentado. Gates de aceite para entrar na camada MCP:
  G1 suporte oficial (mantido pelo próprio projeto, não pela comunidade);
  G2 instalação fácil em user-space, sem containers ou sidecars complexos;
  G3 uso pelo menos tão bom quanto o CLI atual; G4 funciona nativamente em
  Windows e WSL/Linux, ou com ponte simples — ponte complexa significa só CLI.
  O mecanismo de fallback será definido na fase de arquitetura.
- **D5 — Sequência**: bumps de versão primeiro; verificação do codebase-memory
  e revisão arquitetural depois, pois dependem da 0.10.8 instalada.
- **D6 — Entrega da revisão arquitetural (D4)**: relatório com veredito por
  ferramenta + proposta do mecanismo de fallback; implementação só após
  aprovação humana, virando tasks novas.

## Task List

### Phase 1: Bumps de versão

#### Task 1: Atualizar constantes e URL do PortableGit em core.py

**Description:** Alterar as três constantes de versão em
`src/opencode_config/bootstrap/installers/core.py` e ajustar a construção da
URL/nome do asset do git, que deixa de usar o sufixo `.windows.1` fixo e passa
a derivar o nome do arquivo a partir da versão completa.

**Valores novos:**
- `PANDOC_VERSION = "3.11"`
- `PORTABLE_GIT_VERSION = "2.55.0.windows.5"`
- `CODEBASE_MEMORY_VERSION = "0.10.8"`

**Construção do git (substituir as f-strings atuais):**
- tag de download: `v{PORTABLE_GIT_VERSION}` (remover o `.windows.1` fixo)
- nome do asset: `PortableGit-{PORTABLE_GIT_VERSION.replace('.windows.', '.')}-64-bit.7z.exe`,
  que produz `PortableGit-2.55.0.5-64-bit.7z.exe`

**Acceptance criteria:**
- [ ] As três constantes têm os valores novos
- [ ] A URL do git gera `v2.55.0.windows.5` e o asset `PortableGit-2.55.0.5-64-bit.7z.exe`
- [ ] A URL do pandoc gera `3.11` nos dois assets (linux e windows)

**Verification:**
- [ ] `.venv/bin/python -c "from opencode_config.bootstrap.installers.core import PANDOC_VERSION, PORTABLE_GIT_VERSION, CODEBASE_MEMORY_VERSION; print(PANDOC_VERSION, PORTABLE_GIT_VERSION, CODEBASE_MEMORY_VERSION)"`

**Dependencies:** None

**Files likely touched:**
- `src/opencode_config/bootstrap/installers/core.py`

**Estimated scope:** Small (1 arquivo)

#### Task 2: Atualizar strings copiáveis no registry.py e a tabela do README.md

**Description:** Sincronizar as versões hardcoded nas strings `manual_commands`
de `registry.py` (codebase-memory-mcp, pandoc, git) e a linha do
codebase-memory-mcp na tabela de dependências do `README.md`.

**Ocorrências em `registry.py`:**
- codebase-memory-mcp: `@0.9.0` -> `@0.10.8` (2 ocorrências, LINUX e WINDOWS)
- pandoc: `3.7.0.2` -> `3.11` (4 ocorrências, LINUX e WINDOWS)
- git: `PortableGit-2.53.0-64-bit.7z.exe` -> `PortableGit-2.55.0.5-64-bit.7z.exe`
  e `v2.53.0.windows.1` -> `v2.55.0.windows.5`

**Ocorrência em `README.md`:**
- `| codebase-memory-mcp 0.9.0 |` -> `| codebase-memory-mcp 0.10.8 |`

**Acceptance criteria:**
- [ ] Nenhuma ocorrência de `0.9.0`, `3.7.0.2` ou `2.53.0` permanece em `registry.py` nem `README.md`
- [ ] As strings continuam sem prosa (markers do teste `test_detect.py` seguem válidos)

**Verification:**
- [ ] `grep -rn "0\.9\.0\|3\.7\.0\.2\|2\.53\.0" src/opencode_config/bootstrap/registry.py README.md` retorna vazio

**Dependencies:** None (paralela à Task 1)

**Files likely touched:**
- `src/opencode_config/bootstrap/registry.py`
- `README.md`

**Estimated scope:** Small (2 arquivos)

#### Task 3: Atualizar teste do codebase-memory e cobrir o novo asset do git

**Description:** Atualizar o teste que verifica o pin do codebase-memory-mcp e
adicionar teste unitário para a nova URL/nome do asset do PortableGit (D1).

**Mudanças em `tests/bootstrap/test_installers.py`:**
- linha do assert `codebase-memory-mcp@0.9.0` -> `@0.10.8`
- novo teste `test_install_git_builds_windows_portable_asset_url`: usar
  `make_context(tmp_path, environment=EnvironmentKind.WINDOWS)`, fetcher fake
  que registra a URL e escreve bytes vazios (padrão já usado em
  `test_libgomp_runtime_rejects_a_package_checksum_mismatch`) e
  `successful_runner(commands)` (helper existente na linha 61); assert da URL
  capturada igual a
  `https://github.com/git-for-windows/git/releases/download/v2.55.0.windows.5/PortableGit-2.55.0.5-64-bit.7z.exe`

**Acceptance criteria:**
- [ ] Teste do codebase-memory-mcp referencia `@0.10.8`
- [ ] Novo teste do git valida tag e nome do asset derivados de D1
- [ ] Suíte completa do ambiente corrente passa: `.venv/bin/pytest -m all`

**Verification:**
- [ ] `.venv/bin/pytest -m all` verde no ambiente alvo

**Dependencies:** Task 1 e Task 2

**Files likely touched:**
- `tests/bootstrap/test_installers.py`

**Estimated scope:** Small (1 arquivo)

### Checkpoint: Fase 1 concluída
- [ ] `.venv/bin/pytest -m all` passa sem regressão
- [ ] Commit da unidade lógica: bump dos pins do bootstrap (core.py, registry.py, README, testes)

### Phase 2: Verificação do codebase-memory 0.10.8

#### Task 4: Verificação empírica da 0.10.8 e relatório de oportunidades

**Description:** instalar a 0.10.8 em user-space, verificar o comportamento
real da lib e consolidar um relatório de oportunidades para o humano.

**Execução:**
- Atualizar a instalação user-space:
  `npm install --global --prefix "$HOME/.local" codebase-memory-mcp@0.10.8`
- `codebase-memory-mcp --version` e `--help` (inventariar subcomandos e tools do cli)
- Confirmar a API: `search_graph` com `name_pattern`; testar se `query` ainda
  é aceito; `trace_path` com `direction` inbound/outbound
- Verificar se `~/.chrondb` é criado após instalação e indexação (se não for,
  `fix_chrondb_lib` é código morto)
- `codebase-memory-mcp config list` (chaves: `auto_index`, `auto_watch`,
  `watcher_enabled`, `auto_index_limit`)
- Testar no repo indexado 1-2 tools novas (`semantic_query`, `detect_changes`
  ou o que o help listar)
- Reindexar se necessário:
  `codebase-memory-mcp cli index_repository '{"repo_path":"<raiz absoluta>"}'`

**Acceptance criteria:**
- [ ] Relatório apresentado ao humano cobrindo: API real (parâmetros), destino
      do `.chrondb`, tools novas disponíveis no cli, configs disponíveis e
      recomendações de otimização
- [ ] Conclusões registradas no arquivo de plano como insumo das tasks 5-7

**Verification:**
- [ ] Saídas dos comandos anexadas ao relatório

**Dependencies:** Fase 1 concluída

**Files likely touched:**
- Nenhum do repo (relatório na conversa; conclusões no plano)

**Estimated scope:** Small

#### Task 5: Correções de baixo risco na skill e no installer

**Description:** aplicar as correções confirmadas pela verificação da Task 4.

**Mudanças:**
- `harness-conf/skills/code-explorer-priority/SKILL.md`: corrigir
  `search_graph` para `name_pattern` (regex) e `trace_path` com `direction`;
  conferir todos os exemplos da skill contra a API 0.10 real
- `tests/skills/test_code_explorer.py`: atualizar `CLI_COMMANDS` (linha 13)
  para os exemplos corrigidos
- SE `.chrondb` confirmado ausente na 0.10.8: remover `fix_chrondb_lib` de
  `core.py`, a chamada em `install_codebase_memory`, o export em
  `installers/__init__.py`; em `test_installers.py`, limpar a parte do
  chrondb de `test_install_codebase_memory_enables_auto_index` (manter o
  assert do `config set auto_index true`) e remover
  `test_fix_chrondb_lib_moves_runtime_files_from_temp_directory`
- SE `.chrondb` ainda existir: manter tudo e registrar no relatório

**Acceptance criteria:**
- [ ] Skill documenta a API real da 0.10 (`name_pattern`, `direction`)
- [ ] Testes de skill atualizados e verdes
- [ ] `fix_chrondb_lib` removido (ou justificado) conforme verificação
- [ ] `.venv/bin/pytest -m all` verde

**Verification:**
- [ ] Suíte completa no ambiente corrente

**Dependencies:** Task 4

**Files likely touched:**
- `harness-conf/skills/code-explorer-priority/SKILL.md`
- `tests/skills/test_code_explorer.py`
- `src/opencode_config/bootstrap/installers/core.py`
- `src/opencode_config/bootstrap/installers/__init__.py`
- `tests/bootstrap/test_installers.py`

**Estimated scope:** Medium (4-5 arquivos)

### Checkpoint: Fase 2 concluída
- [ ] Relatório entregue e correções aplicadas
- [ ] Commits: correção da skill (docs/config) e remoção do workaround
      (refactor) como unidades lógicas separadas

### Phase 3: Revisão arquitetural multi-harness (D4)

#### Task 6: Levantamento por ferramenta com gates G1-G4

**Description:** para cada ferramenta externa invocada por skills/commands
(codebase-memory-mcp, playwright, crwl/crawl4ai, docling, pandoc, aws-cli),
verificar: modo MCP existe? é oficial? instalação user-space é fácil em
Windows e WSL/Linux? o uso é tão bom quanto o CLI? Aplicar os gates G1-G4 da
decisão de arquitetura multi-harness e emitir veredito por ferramenta com
evidência.

**Notas:**
- crawl4ai é pré-reprovado por G1 (sem MCP oficial no último levantamento);
  re-verificar apenas se houver anúncio oficial
- playwright tem MCP oficial (`@playwright/mcp`); G3 precisa de re-verificação
  (registro anterior: pior que o modo CLI)

**Acceptance criteria:**
- [ ] Tabela por ferramenta: modo MCP (sim/não), oficial (sim/não),
      instalação, multi-SO, veredito (entra na camada MCP / fica só CLI) e
      fonte oficial citada

**Verification:**
- [ ] Fontes oficiais citadas por ferramenta

**Dependencies:** Fase 2 (insumos do codebase-memory real)

**Files likely touched:**
- Nenhum (relatório)

**Estimated scope:** Medium (pesquisa)

#### Task 7: Design do mecanismo de fallback e proposta de arquitetura

**Description:** propor como o fallback MCP -> CLI funciona e como as configs
são materializadas por harness. Opções a avaliar: (a) detecção em runtime
pela skill (instruir: tool MCP se disponível no harness, senão CLI via Bash);
(b) config-time pelo adapter/bootstrap (detectar harness e capacidade,
materializar config e instruções específicas, padrão atual dos adapters);
(c) híbrido. Incluir onde a config MCP viveria (seção `mcp` do
`opencode.json`; `~/.copilot/mcp-config.json`) e quem escreve (bootstrap /
adapter próprio vs install nativo da ferramenta). Trade-offs multi-SO incluídos.

**Acceptance criteria:**
- [ ] Proposta com opções, trade-offs e recomendação
- [ ] Humano aprova ou rejeita; o que for aprovado vira tasks novas de
      implementação (fora do escopo deste plano)

**Verification:**
- [ ] Proposta apresentada; decisão registrada no plano

**Dependencies:** Task 6

**Files likely touched:**
- Nenhum (proposta)

**Estimated scope:** Medium

### Checkpoint: Fase 3 concluída
- [ ] Relatório + proposta entregues; decisão humana registrada no plano
- [ ] Implementação aprovada (se houver) vira plano/tasks novas

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| codebase-memory-mcp 0.9 -> 0.10 tem breaking change na CLI | Médio | Task 4 verifica a API real antes das correções; suíte cobre o binário |
| Divergência de versão entre core.py e registry.py | Médio | Tasks 1 e 2 atualizam ambos; verificação por grep sem versões antigas |
| Nome do asset do git muda com `.windows.5` (`.5` no arquivo) | Médio | Teste dedicado valida a URL construída |
| pandoc 3.11 é major (3.7 -> 3.11) | Baixo | Assets confirmados; md-export usa pandoc de forma estável |
| Remover `fix_chrondb_lib` sem confirmação | Médio | Remoção condicional à verificação empírica da Task 4 |
| Corrigir a skill com API ainda não confirmada | Médio | Task 5 só roda após a Task 4 validar `name_pattern`/`direction` |
| MCP nativo conflitar com o adapter do repo | Alto | Fase 3 é só relatório; implementação exige aprovação humana (D6) |
| MCP de comunidade ou ponte WSL complexa | Alto | Gates G1-G4 da decisão multi-harness reprovam por padrão |

## Open Questions

Nenhuma pendente.
