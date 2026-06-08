# opencode-config

Repo com as configuracoes globais do OpenCode para este usuario/maquina.

## Como funciona

- O OpenCode le as configuracoes globais a partir de `~/.config/opencode`.
- Este repo e a fonte de verdade e pode ficar em qualquer caminho local.
- O bootstrap cria links simbolicos em `~/.config/opencode` apontando para este repo.

## Bootstrap

Depois de clonar este repo, rode:

```bash
./scripts/bootstrap_repo/configurar-repo.sh --yes
```

O script executa quatro fases:
1. **Instala dependencias** (`scripts/bootstrap_repo/wsl-install-deps.sh`)
2. **Configura GitHub Copilot (WSL)** (`scripts/bootstrap_repo/wsl-copilot-sync.sh`)
3. **Cria links simbolicos** (`scripts/bootstrap_repo/opencode-link.sh`)
4. **Instala MCPs** — crawl4ai, codebase-memory, doctree

Cada parte pode ser pulada via variaveis de ambiente:
- `OPENCODE_SKIP_DEPS=1` — pula instalacao de dependencias
- `OPENCODE_SKIP_COPILOT_SYNC=1` — pula sincronizacao Copilot
- `OPENCODE_SKIP_LINKS=1` — pula criacao de links
- `OPENCODE_SKIP_CRAWL4AI=1` — pula configuracao do MCP crawl4ai
- `OPENCODE_SKIP_CODEBASE_MEMORY=1` — pula configuracao do MCP codebase-memory
- `OPENCODE_SKIP_DOCTREE=1` — pula configuracao do MCP doctree

Para aplicar a variavel `OPENCODE_ENABLE_EXA` no shell atual:

```bash
source ~/.bashrc
```

No ambiente WSL deste repo, o script faz duas coisas:

- cria/atualiza os links simbolicos em `~/.config/opencode`
- garante `export OPENCODE_ENABLE_EXA=1` em `~/.bashrc`

Para aplicar a variavel no shell atual depois do bootstrap:

```bash
source ~/.bashrc
```

## O que o script faz

O `configurar-repo.sh` cria links simbolicos em `~/.config/opencode`:

- `~/.config/opencode/agents` -> `agents`
- `~/.config/opencode/commands` -> `commands`
- `~/.config/opencode/opencode.json` -> `opencode.json`
- `~/.config/opencode/skills` -> `skills`
- `~/.config/opencode/scripts` -> `scripts`

O arquivo `AGENTS.md` e local a este repo e **nao** e linkado globalmente.

Se ja existir algo nesses destinos, o script move o conteudo anterior para um backup em `~/.config/opencode-backup/<timestamp>` antes de recriar os links.

## Variaveis de ambiente

- `OPENCODE_ENABLE_EXA=1`: habilita a tool `websearch` do OpenCode via Exa AI

Sem essa variavel, a tool `websearch` nao aparece no runtime quando o provider nao e o nativo do OpenCode.

## Dependencias das skills

Sincronizadas automaticamente pelo bootstrap (`configurar-repo.sh -> wsl-install-deps.sh`).

Instaladas automaticamente (quando possivel):

- `bats`
- `pipx`
- `docling`
- `playwright`
- `bun`
- `codebase-memory-mcp`
- `doctree`
- `bats-support`
- `bats-assert`
- `bats-file`
- `mcp (avelino)`

O bootstrap tambem instala skills de codebase-memory (4 skills) e doctree
(3 skills) em `~/.config/opencode/skills/`,
habilitando comandos `/` de indexacao e busca.

As libs auxiliares do BATS sao instaladas em `~/.local/lib/bats` e o
script garante `BATS_LIB_PATH="$HOME/.local/lib/bats"` no `~/.bashrc`.

Requer **Ubuntu 22.04+** (ou equivalente com Python >= 3.10).

Pacotes que precisam de `sudo` no Ubuntu/WSL:

```bash
sudo apt-get update && sudo apt-get install -y \
  make pandoc pipx \
  tesseract-ocr ocrmypdf ghostscript qpdf librsvg2-bin
```

Dependencia externa fora desse comando:

- AWS CLI v2 para `aws-sso-login` e `aws-add-account-sso`

Para rodar so a verificacao de dependencias:

```bash
./scripts/bootstrap_repo/wsl-install-deps.sh
```

## Configuracao GitHub Copilot

### VS Code Server (WSL) — executado automaticamente

O bootstrap (`configurar-repo.sh`) sincroniza automaticamente para
`~/.copilot/`:
- `prompts/`, `agents/`, `commands/`, `skills/` → sincronizados
- `mcp.json` → `~/.vscode-server/data/User/mcp.json`
- `servers.json` → `~/.config/mcp/servers.json`

Importante:

- o fluxo canônico deste repo usa o wrapper CLI `mcp` (`avelino/mcp`)
- portanto, o arquivo crítico para MCPs no WSL é `~/.config/mcp/servers.json`
- `~/.vscode-server/data/User/mcp.json` é mantido para compatibilidade do Copilot

Para rodar apenas esta parte:

```bash
./scripts/bootstrap_repo/wsl-copilot-sync.sh --yes
```

### VS Code Windows — opcional

Para configurar o VS Code Copilot Windows com os mesmos agents, skills,
commands e instructions (

```powershell
.\scripts\bootstrap_repo\copilot-sync.ps1
```

O script requer PowerShell 5.1+ (nativo no Windows 10/11).

O que e sincronizado para VS Code Windows:

- `skills/*/` → `~/.copilot/skills/` (padrao agentskills.io — sem conversao)
- `agents/*.md` → `%APPDATA%\Code\User\prompts\*.agent.md`
- `commands/*.md` → `%APPDATA%\Code\User\prompts\*.prompt.md`
- `.github/copilot-specific.instructions.md` → `~/.copilot/instructions/copilot-specific.instructions.md`
- MCPs Copilot `exa` e `crawl4ai` → `%APPDATA%\Code\User\mcp.json` (merge, sem sobrescrever)
- MCPs CLI `crawl4ai`, `codebase-memory` e `doctree` → `%USERPROFILE%\.config\mcp\servers.json` (merge, sem sobrescrever)

Para aplicar sem confirmacao interativa:

```powershell
.\scripts\bootstrap_repo\copilot-sync.ps1 -Yes
```

## Testes

Alvos disponiveis:

```bash
make help
make test-opencode
make test-copilot
make test-unit
make test-tools
make test-opencode-integration
make test-copilot-integration
```

Resumo dos alvos:

- `make test-opencode`: roda todos os testes para OpenCode (unit + tools + integracao)
- `make test-copilot`: roda todos os testes para Copilot (unit + tools + integracao)
- `make test-unit`: testes unitarios puros — sem dependencias externas
- `make test-tools`: testes que requerem ferramentas instaladas no WSL
- `make test-opencode-integration`: Camada 2 via API HTTP do OpenCode (requer Docker)
- `make test-copilot-integration`: testes de integracao Copilot CLI (requer copilot e mcp no PATH)

### Testes de integração (Camada 2)

Os testes de integração exigem um modelo configurado explicitamente. Por segurança,
**não há modelo padrão** — você deve escolher conscientemente qual modelo usar.

**Opção 1: modelo próprio (recomendado)**

```bash
export OPENCODE_TEST_MODEL='openai/gpt-4'
make test-opencode-integration
```

**Opção 2: atalho para modelo aberto padrão (apenas ambientes não-sensíveis)**

```bash
make test-opencode-integration-default-model
```

> **AVISO**: O modelo aberto padrão (`opencode/big-pickle`) é um modelo externo
> que **COLETA DADOS** enviados a ele. **Nunca use em ambientes corporativos ou
> com dados sensíveis.** Use apenas para testes pessoais ou de demonstração.

**Opção 3: rodar tudo (unit + tools + integração)**

```bash
export OPENCODE_TEST_MODEL='openai/gpt-4'
make test-opencode
```

### Controle manual do container

```bash
bash tests/opencode-int-test/docker/container-test-opencode.sh --up
bash tests/opencode-int-test/docker/container-test-opencode.sh --down
```

Os testes usam `bats` do PATH e bibliotecas auxiliares instaladas pelo
bootstrap em `~/.local/lib/bats`.

Documentação do framework: [BATS-core](https://bats-core.readthedocs.io/)

Pre-requisitos:

- `make`
- `jq` (para testes de integração)
- dependencias externas conforme o alvo escolhido
