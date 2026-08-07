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
2. **Executa o adapter Copilot CLI** (`adapters/copilot-cli/copilot-cli-adapter.sh`)
3. **Executa o adapter OpenCode** (`adapters/opencode/opencode-adapter.sh`)
4. **Instala ferramentas globais** — `crwl` e `codebase-memory-mcp`

Cada parte pode ser pulada via variaveis de ambiente:
- `OPENCODE_SKIP_DEPS=1` — pula instalacao de dependencias
- `OPENCODE_SKIP_COPILOT_ADAPTER=1` — pula o adapter Copilot CLI
- `OPENCODE_SKIP_OPENCODE_ADAPTER=1` — pula o adapter OpenCode
- `OPENCODE_SKIP_CODEBASE_MEMORY=1` — pula configuracao do codebase-memory CLI

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

Se ja existir algo nesses destinos, o script move o conteudo anterior para um
backup em `~/.config/opencode-backup/<timestamp>` antes de recriar os links.

## Variaveis de ambiente

- `OPENCODE_ENABLE_EXA=1`: habilita a tool `websearch` do OpenCode via Exa AI

Sem essa variavel, a tool `websearch` nao aparece no runtime quando o provider nao e o nativo do OpenCode.

## Dependencias das skills

Sincronizadas automaticamente pelo bootstrap (`configurar-repo.sh -> wsl-install-deps.sh`).

Instaladas automaticamente (quando possivel):

- `bats`
- `pipx`
- `crawl4ai` (`crwl`) e o browser via `crawl4ai-setup`
- `docling`
- `playwright`
- `bun`
- `codebase-memory-mcp`
- `aws-cli` v2 (dependencia obrigatoria gerenciada pelo bootstrap)
- `bats-support`
- `bats-assert`
- `bats-file`

O bootstrap instala o `codebase-memory-mcp` como CLI nativo e habilita o
auto-index no proprio binario.

As libs auxiliares do BATS sao instaladas em `~/.local/lib/bats` e o
script garante `BATS_LIB_PATH="$HOME/.local/lib/bats"` no `~/.bashrc`.

Requer **Ubuntu 22.04+** (ou equivalente com Python >= 3.10).

Pacotes que precisam de `sudo` no Ubuntu/WSL:

```bash
sudo apt-get update && sudo apt-get install -y \
  make pandoc pipx \
  tesseract-ocr ocrmypdf ghostscript qpdf librsvg2-bin
```

O AWS CLI v2 e usado por `aws-sso-login` e `aws-add-account-sso`.

Para rodar so a verificacao de dependencias:

```bash
./scripts/bootstrap_repo/wsl-install-deps.sh
```

## Adapters

O repositório mantém uma fonte canônica e adapters por plataforma:

| Adapter | Entrada | Destino |
|---|---|---|
| `adapters/opencode/` | agents, skills, commands e configuração | links em `~/.config/opencode/` |
| `adapters/copilot-cli/` | fonte canônica transformada | `~/.copilot/` |

O adapter OpenCode cria links simbólicos. O adapter Copilot CLI converte
frontmatter de agentes, transforma commands em skills, valida skills no padrão
agentskills.io e copia artefatos auxiliares.

Use diretamente:

```bash
./adapters/opencode/opencode-adapter.sh --yes
./adapters/copilot-cli/copilot-cli-adapter.sh --yes
```

No Windows, a versão PowerShell do adapter Copilot CLI é:

```powershell
.\adapters\copilot-cli\copilot-cli-adapter.ps1 -Yes
```

Destinos sincronizados pelo Copilot CLI:

- `agents/*.md` → `~/.copilot/agents/*.agent.md`
- `commands/*.md` → `~/.copilot/skills/*/SKILL.md`
- `skills/*/` → `~/.copilot/skills/`
- `agents/default-artifacts/` → `~/.copilot/agents/default-artifacts/`
- `.github/copilot-specific.instructions.md` → `~/.copilot/instructions/`

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
- `make test-opencode-integration`: Camada 2 via API HTTP do OpenCode
- `make test-copilot-integration`: testes de integracao Copilot CLI (requer copilot no PATH)

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

Os testes usam `bats` do PATH e bibliotecas auxiliares instaladas pelo
bootstrap em `~/.local/lib/bats`.

Documentação do framework: [BATS-core](https://bats-core.readthedocs.io/)

Pre-requisitos:

- `make`
- `jq` (para testes de integração)
- dependencias externas conforme o alvo escolhido
