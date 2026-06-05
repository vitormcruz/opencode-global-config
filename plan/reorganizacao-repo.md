# Plano de Reorganizacao — `opencode-config`

## Sumario Executivo

| Fase | Nome | Arquivos afetados | Depende de |
|------|------|-------------------|------------|
| 1 | Renomear `vscode` -> `copilot` | 8 arquivos + 4 renames | Nenhuma |
| 2 | Separar instrucoes (auditoria + regra de precedencia) | 2 arquivos | Fase 1 |
| 3 | Nova arquitetura de testes | Makefile + 3 novos arquivos | Fase 1 |
| 4 | Estrategia MCP/Copilot (documentar + testar) | 2 arquivos novos | Fase 1, 3 |
| 5 | Copilot CLI — pesquisa + plano de testes de integracao | Documentacao (plano) | Fase 3, 4 |

---

## FASE 1: Renomear `vscode` -> `copilot`

### 1.1 Arquivos a renomear (`git mv`)

```
scripts/bootstrap_repo/vscode-sync.ps1      -> copilot-sync.ps1
scripts/bootstrap_repo/wsl-vscode-sync.sh   -> wsl-copilot-sync.sh
tests/scripts/bootstrap_repo/vscode-sync-test.bats    -> copilot-sync-test.bats
tests/scripts/bootstrap_repo/wsl-vscode-sync-test.bats -> wsl-copilot-sync-test.bats
```

### 1.2 Edicoes — `scripts/bootstrap_repo/configurar-repo.sh`

| Linha | De | Para |
|-------|----|------|
| 4 | `VS Code sync (wsl)` | `Copilot sync (wsl)` |
| 26 | `Configura VS Code Server` | `Configura GitHub Copilot (WSL)` |
| 40 | `OPENCODE_SKIP_VSCODE_SYNC` | `OPENCODE_SKIP_COPILOT_SYNC` |
| 59 | `wsl_vscode_script` | `wsl_copilot_script` |
| 59 | `wsl-vscode-sync.sh` | `wsl-copilot-sync.sh` |
| 103 | `run_vscode_sync` | `run_copilot_sync` |
| 104 | `OPENCODE_SKIP_VSCODE_SYNC` | `OPENCODE_SKIP_COPILOT_SYNC` |
| 105 | `"SKIP: Sincronizacao VS Code Server (OPENCODE_SKIP_VSCODE_SYNC=1)"` | `"SKIP: Sincronizacao Copilot (OPENCODE_SKIP_COPILOT_SYNC=1)"` |
| 109 | `"wsl-vscode-sync.sh"` | `"wsl-copilot-sync.sh"` |
| 111 | `"Configurando VS Code Server (WSL)"` | `"Configurando GitHub Copilot (WSL)"` |
| 113 | `~/.vscode-server/data/User/` | `~/.copilot/` |
| 118 | `"$wsl_vscode_script"` | `"$wsl_copilot_script"` |
| 201 | `run_vscode_sync` | `run_copilot_sync` |
| 201 | `"Falha na sincronizacao VS Code"` | `"Falha na sincronizacao Copilot"` |
| 212 | `~/.vscode-server/data/User/prompts/` | `~/.copilot/prompts/` |
| 214 | `"Para VS Code Windows (opcional)"` | `"Para Copilot Windows (opcional)"` |
| 215 | `vscode-sync.ps1` | `copilot-sync.ps1` |

### 1.3 Edicoes — `scripts/bootstrap_repo/wsl-vscode-sync.sh` (apos renomear)

| Linha | De | Para |
|-------|----|------|
| 2 | `wsl-vscode-sync.sh` | `wsl-copilot-sync.sh` |
| 3 | `VS Code Server (WSL)` | `GitHub Copilot (WSL)` |
| 5 | `wsl-vscode-sync.sh` | `wsl-copilot-sync.sh` |
| 12 | `vscode_dir=` | `copilot_dir=` |
| 12 | `~/.vscode-server/data/User` | `~/.copilot` |
| 13 | `backup_dir=` | `backup_dir=` |
| 13 | `~/.vscode-server/data/User/.backups/` | `~/.copilot/.backups/` |
| 26 | `wsl-vscode-sync` | `wsl-copilot-sync` |
| 28 | `VS Code Server WSL` | `GitHub Copilot (WSL)` |
| 31 | `wsl-vscode-sync.sh` | `wsl-copilot-sync.sh` |
| 39 | `~/.vscode-server/data/User/` | `~/.copilot/` |
| 151 | `~/.vscode-server/data/User/` | `~/.copilot/` |
| todas refs | `$vscode_dir` (linhas 160,165,171,191,203,234,240) | `$copilot_dir` |

### 1.4 Edicoes — `scripts/bootstrap_repo/vscode-sync.ps1` (apos renomear)

| Linha | De | Para |
|-------|----|------|
| 4 | `VS Code (Windows)` | `GitHub Copilot (Windows)` |
| 8 | `VS Code` | `Copilot` |
| 26 | `vscode-sync.ps1 -Yes` | `copilot-sync.ps1 -Yes` |
| 44 | `vscode-sync.ps1` | `copilot-sync.ps1` |
| 46 | `VS Code (Windows)` | `GitHub Copilot (Windows)` |
| 49 | `vscode-sync.ps1 [-Yes]` | `copilot-sync.ps1 [-Yes]` |
| 81 | `"vscode-backup"` | `"copilot-backup"` |
| 87 | `.config\vscode-backup` | `.config\copilot-backup` |
| 274 | `Adapt-SkillForVSCode` func | `Adapt-SkillForCopilot` (4 refs internas) |

### 1.5 Edicoes — `README.md`

| Linha | De | Para |
|-------|----|------|
| 21 | `Configura VS Code Server WSL` | `Configura GitHub Copilot (WSL)` |
| 21 | `wsl-vscode-sync.sh` | `wsl-copilot-sync.sh` |
| 115-152 | Toda secao `## Configuracao VS Code` | `## Configuracao GitHub Copilot` |
| 120 | `~/.vscode-server/data/User/` | `~/.copilot/` |
| 127 | `wsl-vscode-sync.sh` | `wsl-copilot-sync.sh` |
| 136 | `.\\scripts\\bootstrap_repo\\vscode-sync.ps1` | `.\\scripts\\bootstrap_repo\\copilot-sync.ps1` |
| 152 | `.\\scripts\\bootstrap_repo\\vscode-sync.ps1 -Yes` | `.\\scripts\\bootstrap_repo\\copilot-sync.ps1 -Yes` |
| 27 | `OPENCODE_SKIP_VSCODE_SYNC` | `OPENCODE_SKIP_COPILOT_SYNC` |

### 1.6 Edicoes — `tests/scripts/bootstrap_repo/repo-structure-test.bats`

| Linha | De | Para |
|-------|----|------|
| 269 | `wsl-vscode-sync.sh e executavel` | `wsl-copilot-sync.sh e executavel` |
| 270 | `wsl-vscode-sync.sh` | `wsl-copilot-sync.sh` |

### 1.7 Edicoes — `tests/scripts/bootstrap_repo/vscode-sync-test.bats` (apos renomear)

- Renomear prefixo de todos os 12 testes: `"vscode-sync:"` -> `"copilot-sync:"`
- Linha 2: `vscode-sync.ps1` -> `copilot-sync.ps1`
- Linha 50: `vscode-sync.ps1` -> `copilot-sync.ps1`

### 1.8 Edicoes — `tests/scripts/bootstrap_repo/wsl-vscode-sync-test.bats` (apos renomear)

- Renomear prefixo de todos os 10 testes: `"wsl-vscode-sync"` -> `"wsl-copilot-sync"`
- Linhas 2, 6, 30: `wsl-vscode-sync` -> `wsl-copilot-sync`
- Linha 11: `~/.vscode-server/data/User` -> `~/.copilot`
- Linhas 53, 59: `~/.vscode-server/` -> `~/.copilot/`

### 1.9 NAO renomear — `skills/git-workflow-and-versioning/SKILL.md:256`

`.vscode/settings.json` e referencia ao diretorio de config **do VS Code IDE**,
nao a configuracao do Copilot. Deve permanecer como esta.

### Checklist Fase 1

- [ ] `git mv` dos 4 arquivos (scripts + testes)
- [ ] Editar `configurar-repo.sh` (18 mudancas)
- [ ] Editar `wsl-copilot-sync.sh` (18 mudancas)
- [ ] Editar `copilot-sync.ps1` (10 mudancas)
- [ ] Editar `README.md` (8 mudancas)
- [ ] Editar `repo-structure-test.bats` (2 mudancas)
- [ ] Editar `copilot-sync-test.bats` (14 mudancas)
- [ ] Editar `wsl-copilot-sync-test.bats` (12 mudancas)
- [ ] Rodar `make test-unit` para validar
- [ ] Rodar `make test-tools` para validar

---

## FASE 2: Auditoria e Separacao de Instrucoes

### 2.1 Auditoria de conteudo atual

| Regra/Instrucao | AGENTS.md | copilot-specific | OK? |
|-----------------|-----------|-----------------|-----|
| Idioma PT-BR | Sim | — | OK |
| "configure este repo" atalho | Sim | — | OK (generico, usa `bash`) |
| Links simbolicos | Sim | — | OK (generico, ambas ferramentas leem paths) |
| Concisao | Sim | — | OK |
| Geracao MD (120 cols) | Sim | — | OK |
| Exibicao copia-e-cola | Sim | — | OK |
| Acao (sem confirmacao) | Sim | — | OK |
| Commits (conventional, caveman) | Sim | — | OK |
| Criacao de Skills | Sim | — | OK |
| Sinc Workflow <-> Agentes | Sim | — | OK |
| Regras de Testes | Sim | — | OK |
| README manutencao | Sim | — | OK |
| Upstream de Skills | Sim | — | OK |
| MCP via CLI (avelino/mcp) | — | Sim | OK |
| Servidores MCP disponiveis | — | Sim | OK |
| Skills `/` do Copilot | — | Sim | OK |
| Referencia a AGENTS.md | — | Sim (linha 5) | OK |

### 2.2 Problemas encontrados

1. **Duplicacao**: As listas de servidores MCP (`crawl4ai`, `codebase-memory`,
   `doctree`) estao no `copilot-specific.instructions.md`. O opencode acessa MCP
   nativamente via `opencode.json` — nao precisa de lista duplicada em
   instructions. OK como esta.
2. **AGENTS.md referencia `make test`** (linha 110): sera atualizado para
   `make test-opencode` ou `make test-copilot` conforme a ferramenta em uso
   (ver Fase 3).
3. **Falta regra de precedencia explicita**: nem AGENTS.md nem o
   copilot-specific documentam a ordem de precedencia.

### 2.3 Regra de precedencia

Adicionar ao topo do `AGENTS.md`:

```markdown
# Precedencia de Instrucoes

1. O arquivo especifico de ferramenta (`.github/copilot-specific.instructions.md`)
   **sobrescreve** este AGENTS.md quando ha conflito.
2. Regras nao conflitantes se acumulam — ambos os arquivos sao aplicados.
3. AGENTS.md contem regras **genericas** que valem para qualquer ferramenta
   (OpenCode, GitHub Copilot).
```

### Checklist Fase 2

- [ ] Adicionar secao "Precedencia de Instrucoes" ao AGENTS.md
- [ ] Atualizar `AGENTS.md:110` (referencia `make test` -> `make test-opencode`)
- [ ] Verificar que nao ha contradicao entre AGENTS.md e copilot-specific
- [ ] Atualizar testes de estrutura para validar os 2 arquivos de instrucoes

---

## FASE 3: Nova Arquitetura de Testes

### 3.1 Targets do Makefile

```makefile
# Target removido:
#   make test  (nao deterministico sem contexto de ferramenta)

# Targets mantidos (inalterados):
## Testes unitarios puros - sem dependencias externas
test-unit:
	$(BATS) \
	        $(TESTS_DIR)/agents \
	        $(TESTS_DIR)/scripts/bootstrap_repo/opencode-link-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/repo-state-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/repo-structure-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/configurar-repo-test.bats \
	        $(TESTS_DIR)/scripts/skills \
	        $(TESTS_DIR)/scripts/browser-test \
	        $(TESTS_DIR)/scripts/mapa-produto

## Testes que requerem ferramentas instaladas no WSL
test-tools:
	@printf '\n=== test-tools: requer ferramentas configuradas no WSL ===\n'
	$(BATS) \
	        $(TESTS_DIR)/scripts/opencode-doc-extract-test.bats \
	        $(TESTS_DIR)/scripts/opencode-md-export-test.bats \
	        $(TESTS_DIR)/scripts/opencode-svgtoimage-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/wsl-install-deps-test.bats \
	        $(TESTS_DIR)/scripts/crawl4ai \
	        $(TESTS_DIR)/scripts/codebase-memory \
	        $(TESTS_DIR)/scripts/doctree

# Targets NOVOS:

## OpenCode completo (unit + tools + integracao)
test-opencode: test-unit test-tools test-opencode-integration
	@printf '\n=== test-opencode: concluido ===\n'

## Copilot completo (unit + tools + integracao)
test-copilot: test-unit test-tools test-copilot-integration
	@printf '\n=== test-copilot: concluido ===\n'

## Integracao OpenCode (existente, reuso)
test-opencode-integration:
	@bash -c 'set -e; \
	  if [ -z "$$OPENCODE_TEST_MODEL" ]; then \
	    echo "ERRO: OPENCODE_TEST_MODEL nao definido"; \
	    echo ""; \
	    echo "Opcoes:"; \
	    echo "  1. export OPENCODE_TEST_MODEL=seu-modelo"; \
	    echo "     Exemplo: export OPENCODE_TEST_MODEL=openai/gpt-4"; \
	    echo ""; \
	    echo "  2. make test-opencode-integration-default-model"; \
	    echo "     (usa modelo aberto padrao — ATENCAO: coleta dados externos)"; \
	    exit 1; \
	  fi; \
	  trap "bash tests/opencode-int-test/docker/container-test-opencode.sh --down" EXIT; \
	  bash tests/opencode-int-test/docker/container-test-opencode.sh --up; \
	  $(BATS) $(TESTS_DIR)/opencode-int-test'

## Integracao Copilot (NOVO)
test-copilot-integration:
	@bash -c 'set -e; \
	  if ! command -v copilot >/dev/null 2>&1; then \
	    echo "ERRO: Copilot CLI nao encontrado no PATH"; \
	    echo ""; \
	    echo "Instale com:"; \
	    echo "  npm install -g @github/copilot"; \
	    echo "  copilot --login"; \
	    exit 1; \
	  fi; \
	  if ! command -v mcp >/dev/null 2>&1; then \
	    echo "ERRO: avelino/mcp nao encontrado no PATH"; \
	    echo ""; \
	    echo "Instale via bootstrap:"; \
	    echo "  ./scripts/bootstrap_repo/configurar-repo.sh --yes"; \
	    exit 1; \
	  fi; \
	  $(BATS) $(TESTS_DIR)/copilot-int-test'
```

### 3.2 Novos arquivos de teste

Criar diretorio `tests/copilot-int-test/` espelhando `tests/opencode-int-test/`:

```
tests/copilot-int-test/
  helpers/
    copilot_helper.bash         # shared helpers (mock sandbox, etc.)
  mcp-smoke/
    mcp-smoke-test.bats         # smoke tests via avelino/mcp
  config/
    copilot.test.settings.json
  copilot-cli-test.bats         # smoke: copilot --help
  copilot-mcp-test.bats         # MCP tools via avelino/mcp
  copilot-config-test.bats      # valida paths ~/.copilot/
```

### 3.3 O que compartilhar entre suites

| Componente | Compartilhado? | Como |
|------------|---------------|------|
| `test_helper.bash` | Parcial | Mover funcoes genericas para `tests/helpers/common.bash` |
| MCP mock server (`mcp-mock/`) | Sim | Ja existe, reusar em ambas |
| Fixtures (`test-resources/`) | Sim | Ja compartilhado |
| BATS libraries | Sim | `BATS_LIB_PATH` ja configurado |
| `config/*.test.json` | Nao | Cada ferramenta tem seu config |
| Docker container | Nao | So opencode usa Docker; Copilot usa CLI direto |
| behavioral_helper | Parcial | Extrair assertions genericas para `tests/helpers/` |

### 3.4 Impacto nos testes existentes

| Arquivo | Impacto | Acao |
|---------|---------|------|
| `Makefile` | target `test` removido | Editar |
| `AGENTS.md:110` | Referencia `make test` | Mudar para `make test-opencode` ou `make test-copilot` |
| `README.md` | Secao "Testes" | Reescrever com nova arquitetura |
| `repo-structure-test.bats` | Testes de permissao | Adicionar validacao de novos arquivos |
| `helpers/test_helper.bash` | Refactor | Extrair `common.bash` |

### Checklist Fase 3

- [ ] Reescrever Makefile com novos targets
- [ ] Criar `tests/copilot-int-test/` com estrutura
- [ ] Criar `tests/copilot-int-test/copilot-cli-test.bats`
- [ ] Criar `tests/copilot-int-test/copilot-mcp-test.bats`
- [ ] Criar `tests/helpers/common.bash` extraido de `test_helper.bash`
- [ ] Atualizar `AGENTS.md:110` (referencia `make test`)
- [ ] Atualizar `README.md` secao de testes
- [ ] Adicionar `repo-structure-test.bats` checks para novos arquivos
- [ ] Rodar `make test-unit` e `make test-tools` (nao devem quebrar)
- [ ] Rodar `make test-opencode` para validar
- [ ] Rodar `make test-opencode-integration` para validar (nao deve quebrar)

---

## FASE 4: Estrategia MCP/Copilot

### 4.1 Como funciona hoje

O Copilot possui suporte nativo ao protocolo MCP, mas **nao e possivel utiliza-lo**
no ambiente de uso. Por isso, usamos o wrapper CLI `avelino/mcp` como mecanismo
alternativo:

1. `avelino/mcp` e instalado como wrapper CLI em `~/.local/bin/mcp`
2. `copilot-specific.instructions.md` instrui o agente a usar `mcp --list` e `mcp call`
3. O Copilot executa comandos shell via tool approval e o `mcp` CLI traduz chamadas
   para o protocolo MCP

### 4.2 Documentacao

Adicionar ao `copilot-specific.instructions.md` uma secao de arquitetura:

```markdown
## Arquitetura MCP no Copilot

O GitHub Copilot suporta MCP nativamente, mas nao e possivel utiliza-lo no ambiente
de uso. Para acessar os servidores MCP configurados neste repo, usamos o wrapper CLI
`avelino/mcp` instalado em `~/.local/bin/mcp`.

Fluxo de acesso:
  1. Copilot recebe instrucao para usar uma tool MCP
  2. Copilot executa `mcp --list` para descobrir servidores disponiveis
  3. Copilot executa `mcp call <servidor> <tool> --arg valor`
  4. O wrapper `mcp` traduz a chamada CLI para protocolo MCP
  5. O servidor MCP responde e o resultado e retornado ao Copilot

Servidores acessiveis via `mcp`:
  - crawl4ai (SSE, localhost:11235)
  - codebase-memory (local process)
  - doctree (local process via bunx)
```

### 4.3 Testes de validacao MCP

Os testes de `copilot-int-test/copilot-mcp-test.bats` devem:

1. **Smoke test basico**: `mcp --help` retorna 0
2. **Listagem**: `mcp --list` retorna JSON com servidores esperados
3. **Tool help**: `mcp call crawl4ai crawl4ai_md --help` retorna schema
4. **Tool call simples**: `mcp call crawl4ai crawl4ai_md --url "https://example.com"`
   retorna markdown
5. **Validacao de erro**: tool inexistente retorna erro

### 4.4 Cobertura de servidores MCP

| Servidor | opencode (nativo) | copilot (avelino/mcp) | Teste |
|----------|-------------------|-----------------------|-------|
| crawl4ai | `opencode-int-test/mcp-test.bats` | `copilot-int-test/copilot-mcp-test.bats` | Ambos |
| codebase-memory | `opencode-int-test/mcp-test.bats` | `copilot-int-test/copilot-mcp-test.bats` | Ambos |
| doctree | `opencode-int-test/mcp-test.bats` | `copilot-int-test/copilot-mcp-test.bats` | Ambos |

### Checklist Fase 4

- [ ] Atualizar `copilot-specific.instructions.md` com secao de arquitetura MCP
- [ ] Criar `tests/copilot-int-test/copilot-mcp-test.bats` com smoke tests
- [ ] Garantir que `mcp --list` retorna todos os servidores configurados
- [ ] Garantir que `mcp call <server> <tool> --help` funciona para cada servidor
- [ ] Adicionar `copilot-mcp-test.bats` ao target `test-copilot-integration`

---

## FASE 5: Pesquisa Copilot CLI + Plano de Testes

### 5.1 Resumo da pesquisa

**Nome oficial**: GitHub Copilot CLI (binary: `copilot`, package: `@github/copilot`)
**Repositorio**: `github.com/github/copilot-cli`

**Instalacao** (Linux/WSL):
```bash
# npm (cross-platform)
npm install -g @github/copilot

# Homebrew (macOS/Linux)
brew install copilot-cli

# Script (macOS/Linux)
curl -fsSL https://gh.io/copilot-install | bash

# WinGet (Windows)
winget install GitHub.Copilot
```

**Modos de uso**:
- **Interativo**: `copilot` (entra no TUI)
- **Programatico**: `copilot -p "prompt" --allow-tool=...`
- **Plan mode**: `Shift+Tab` no TUI, ou `/plan` no chat
- **Autopilot**: execucao autonoma sem aprovacao por passo
- **Fleet**: `/fleet` para subagentes paralelos

**Suporte a instrucoes**:
- Projeto: `.github/copilot-instructions.md`
- Global: `~/.copilot/instructions/`
- Custom agents: `*.agent.md` em `.github/agents/` ou `~/.copilot/agents/`

**Suporte a skills**: `~/.copilot/skills/` (compativel com formato agentskills.io —
mesmo que usamos)

**Suporte a MCP**:
- MCP nativo: SIM! Copilot CLI suporta MCP servers via `/mcp add` ou config em
  `.copilot/mcp.json`
- Isso significa que **o `avelino/mcp` wrapper pode se tornar desnecessario** se
  usarmos o Copilot CLI nativamente
- Porem, o Copilot **VS Code extension** (nao CLI) pode nao ter o mesmo suporte

**Suporte a ferramentas**:
- Shell: `--allow-tool='shell(git:*)'`
- Write: `--allow-tool='write'`
- URL fetch: `--allow-tool='url'`
- MCP servers: `--allow-tool='MCP-SERVER-NAME'`

### 5.2 Plano de testes de integracao Copilot CLI

```bash
# Smoke: CLI existe e funciona
copilot --help
copilot --version

# Smoke: MCP nativo (se disponivel no CLI)
copilot -p "list available MCP tools" --allow-tool='shell' -s

# Smoke: MCP via avelino wrapper (fallback)
copilot -p "run mcp --list and report which servers are available" \
  --allow-tool='shell(mcp)' -s

# Teste: execucao programatica com prompt simples
copilot -p "What is 2+2?" -s --model claude-haiku-4.5
```

### 5.3 Observacao importante

O Copilot CLI suporta MCP nativamente, mas esse suporte nao esta disponivel no
ambiente de uso. O wrapper `avelino/mcp` e o mecanismo permanente de acesso a tools
MCP e tambem serve como ferramenta de debug/teste manual.

### Checklist Fase 5

- [ ] Documentar descobertas da pesquisa no `plan/copilot-cli-research.md`
- [ ] Criar `tests/copilot-int-test/copilot-cli-test.bats`
- [ ] Criar `tests/copilot-int-test/copilot-mcp-test.bats`
- [ ] Adicionar scripts de smoke test ao target `test-copilot-integration`
- [ ] Atualizar `wsl-install-deps.sh` para instalar `@github/copilot` (npm) como
      dep opcional
- [ ] Atualizar `copilot-specific.instructions.md` com instrucoes de uso do Copilot
      CLI (alem do VS Code)

---

## Ordem de Execucao Recomendada

```
Fase 1 (rename vscode -> copilot)
  |
  +---> Fase 2 (auditoria + separacao + precedencia)
  |
  +---> Fase 3 (nova arquitetura de testes)
  |        |
  |        +---> Fase 4 (estrategia MCP/Copilot)
  |                 |
  |                 +---> Fase 5 (plano de testes Copilot CLI)
```

Fase 1 e pre-requisito das demais (por causa dos renames nos paths). Fases 2 e 3
sao independentes entre si. Fase 4 depende da 3. Fase 5 depende da 4.

---

## Total de Arquivos

| Tipo | Quantidade |
|------|------------|
| Arquivos a **renomear** (`git mv`) | 4 |
| Arquivos a **editar** | 10 |
| Arquivos a **criar** | 5 |
| Targets Makefile removidos | 1 (`make test`) |
| Targets Makefile novos | 3 (`test-opencode`, `test-copilot`, `test-copilot-integration`) |

---

## Diagrama de Dependencias

```
Fase 1 ──┬──> Fase 2
         │
         ├──> Fase 3 ──> Fase 4 ──> Fase 5
```
