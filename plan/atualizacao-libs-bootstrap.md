# Implementation Plan: Atualização de libs pinadas no bootstrap

## Overview

Atualizar três dependências com versão fixa no bootstrap do repo:
codebase-memory-mcp, pandoc e PortableGit (Windows). As versões vivem em dois
pontos que precisam permanecer sincronizados: as constantes em
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

## Task List

### Phase 1: Constantes e strings

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

### Phase 2: Testes e validação

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

### Checkpoint: suíte verde
- [ ] `.venv/bin/pytest -m all` passa sem regressão

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| codebase-memory-mcp 0.9 -> 0.10 tem breaking change na CLI | Médio | Suíte cobre o binário real; reverter o pin se regredir |
| Divergência de versão entre core.py e registry.py | Médio | Tasks 1 e 2 atualizam ambos; verificação por grep sem versões antigas |
| Nome do asset do git muda com `.windows.5` (`.5` no arquivo) | Médio | Teste dedicado valida a URL construída |
| pandoc 3.11 é major (3.7 -> 3.11) | Baixo | Assets confirmados; md-export usa pandoc de forma estável |

## Open Questions

Nenhuma pendente.
