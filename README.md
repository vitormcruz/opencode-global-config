# opencode-config

Repo com as configuracoes globais do OpenCode para este usuario/maquina.

## Como funciona

- O OpenCode le as configuracoes globais a partir de `~/.config/opencode`.
- Este repo e a fonte de verdade e pode ficar em qualquer caminho local.
- O bootstrap cria links simbolicos em `~/.config/opencode` apontando para este repo.

## Bootstrap

Depois de clonar este repo, rode:

```bash
./scripts/bootstrap_repo/opencode-link
```

No ambiente WSL deste repo, o script faz duas coisas:

- cria/atualiza os links simbolicos em `~/.config/opencode`
- garante `export OPENCODE_ENABLE_EXA=1` em `~/.bashrc`

Para aplicar a variavel no shell atual depois do bootstrap:

```bash
source ~/.bashrc
```

## O que o script faz

O `scripts/bootstrap_repo/opencode-link` conecta estes caminhos:

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

O bootstrap (`opencode-link`) chama automaticamente
`scripts/bootstrap_repo/opencode-install-deps`.

Instaladas automaticamente pelo bootstrap (quando possivel):

- `bats`
- `pipx`
- `docling`
- `playwright`
- `graphifyy`
- `bats-support`
- `bats-assert`
- `bats-file`

As libs auxiliares do BATS sao instaladas em `~/.local/lib/bats` e o
bootstrap garante `BATS_LIB_PATH="$HOME/.local/lib/bats"` no `~/.bashrc`.

Pacotes que precisam de `sudo` no Ubuntu/WSL:

```bash
sudo apt-get update && sudo apt-get install -y \
  make bats pandoc pipx tesseract-ocr ocrmypdf ghostscript qpdf librsvg2-bin
```

Dependencia externa fora desse comando:

- AWS CLI v2 para `aws-sso-login` e `aws-add-account-sso`

Para rodar so a verificação de dependências:

```bash
./scripts/bootstrap_repo/opencode-install-deps
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
- `agents/*.md` → `%APPDATA%\Code\User\prompts\*.agent.md`
- `commands/*.md` → `%APPDATA%\Code\User\prompts\*.prompt.md`
- `AGENTS.md` → `%APPDATA%\Code\User\prompts\opencode-config.instructions.md`
- MCPs `exa` e `crawl4ai` → `%APPDATA%\Code\User\mcp.json` (merge, sem sobrescrever)

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
make test-scripts
make test-bootstrap-repo
make test-opencode-integration
```

Resumo dos alvos:

- `make test`: roda a Camada 1 — todos os testes em `tests/scripts/` (sem Docker)
- `make test-scripts`: idem (alias explicito para `tests/scripts/`)
- `make test-bootstrap-repo`: so os testes de bootstrap do repo
- `make test-opencode-integration`: Camada 2 via API HTTP do OpenCode

Controle manual do container de testes:

```bash
bash tests/opencode-int-test/docker/container-test-opencode.sh --up
bash tests/opencode-int-test/docker/container-test-opencode.sh --down
```

Os testes usam `bats` do PATH e bibliotecas auxiliares instaladas pelo
bootstrap em `~/.local/lib/bats`.

Documentação do framework: [BATS-core](https://bats-core.readthedocs.io/)

Pre-requisitos:

- `make`
- dependencias externas conforme o alvo escolhido
- Docker para a Camada 2 (`make test-opencode-integration`)
