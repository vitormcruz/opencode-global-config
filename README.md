# opencode-config

Repo com as configuracoes globais do OpenCode para este usuario/maquina.

## Como funciona

- O OpenCode le as configuracoes globais a partir de `~/.config/opencode`.
- Este repo e a fonte de verdade e pode ficar em qualquer caminho local.
- O bootstrap cria links simbolicos em `~/.config/opencode` apontando para este repo.

## Bootstrap

Depois de clonar este repo, rode:

```bash
./scripts/bootstrap_repo/opencode-link.sh
```

No ambiente WSL deste repo, o script faz duas coisas:

- cria/atualiza os links simbolicos em `~/.config/opencode`
- garante `export OPENCODE_ENABLE_EXA=1` em `~/.bashrc`

Para aplicar a variavel no shell atual depois do bootstrap:

```bash
source ~/.bashrc
```

## O que o script faz

O `scripts/bootstrap_repo/opencode-link.sh` conecta estes caminhos:

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

O bootstrap (`opencode-link.sh`) chama automaticamente
`scripts/bootstrap_repo/opencode-install-deps.sh`.

Instaladas automaticamente pelo bootstrap (quando possivel):

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

As libs auxiliares do BATS sao instaladas em `~/.local/lib/bats` e o
bootstrap garante `BATS_LIB_PATH="$HOME/.local/lib/bats"` no `~/.bashrc`.

Requer **Ubuntu 22.04+** (ou equivalente com Python >= 3.10).

Pacotes que precisam de `sudo` no Ubuntu/WSL:

```bash
sudo apt-get update && sudo apt-get install -y \
  make pandoc pipx \
  tesseract-ocr ocrmypdf ghostscript qpdf librsvg2-bin
```

Dependencia externa fora desse comando:

- AWS CLI v2 para `aws-sso-login` e `aws-add-account-sso`

Para rodar so a verificação de dependências:

```bash
./scripts/bootstrap_repo/opencode-install-deps.sh
```

## Configuração VS Code

Depois de rodar o bootstrap do OpenCode, rode o script de sincronização para
configurar o VS Code Copilot com os mesmos agents, skills, commands e
instructions deste repo:

```powershell
.\scripts\bootstrap_repo\vscode-sync.ps1
```

O script requer PowerShell 5.1+ (nativo no Windows 10/11).

O que é sincronizado:

- `skills/*/` → `~/.copilot/skills/` (padrão agentskills.io — sem conversão)
- `agents/*.md` → `%APPDATA%\\Code\\User\\prompts\\*.agent.md`
- `commands/*.md` → `%APPDATA%\\Code\\User\\prompts\\*.prompt.md`
- `.github/copilot-specific.instructions.md` → `~/.copilot/instructions/copilot-specific.instructions.md`
- MCPs `exa` e `crawl4ai` → `%APPDATA%\\Code\\User\\mcp.json` (merge, sem sobrescrever)

O arquivo `.github/copilot-specific.instructions.md` é versionado no repo,
contém as instruções MCP via CLI e é sincronizado como instrução global de
usuário do VS Code com `applyTo: "**"`.

Skills com scripts externos (doc-extract, md-export, prompt-improver): o
script copia o executável para dentro da pasta da skill e reescreve a
referência no `SKILL.md` para usar `wsl bash` ou `wsl python`.

Para aplicar sem confirmação interativa:

```powershell
.\scripts\bootstrap_repo\vscode-sync.ps1 -Yes
```

## Testes

Alvos disponiveis:

```bash
make help
make test
make test-unit
make test-tools
make test-opencode-integration
```

Resumo dos alvos:

- `make test`: roda todos os testes (unit + tools + integracao)
- `make test-unit`: testes unitarios puros — sem dependencias externas
- `make test-tools`: testes que requerem ferramentas instaladas no WSL
- `make test-opencode-integration`: Camada 2 via API HTTP do OpenCode (requer Docker)

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
make test
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
- Docker para a Camada 2 (`make test-opencode-integration`)
