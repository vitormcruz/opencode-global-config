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

- `pipx`
- `docling`

Pacotes que precisam de `sudo` no Ubuntu/WSL:

```bash
sudo apt-get update && sudo apt-get install -y \
  make pandoc pipx tesseract-ocr ocrmypdf ghostscript qpdf librsvg2-bin
```

Dependencia externa fora desse comando:

- AWS CLI v2 para `aws-sso-login` e `aws-add-account-sso`

Para rodar so a verificação de dependências:

```bash
./scripts/bootstrap_repo/opencode-install-deps
```

## Testes

Alvos disponiveis:

```bash
make help
make test
make test-unit
make test-integration
make test-bootstrap-repo
make test-mcp
make test-opencode-integration
```

Resumo dos alvos:

- `make test`: roda a Camada 1 (sem Docker)
- `make test-unit`: estrutura estatica
- `make test-integration`: wrappers que dependem de ferramentas externas
- `make test-bootstrap-repo`: testes do bootstrap e do estado final do repo
- `make test-mcp`: testes dos artefatos MCP fora do contexto do OpenCode
- `make test-opencode-integration`: Camada 2 via API HTTP do OpenCode

Controle manual do container de testes:

```bash
bash tests/opencode-int-test/container-test-opencode.sh --up
bash tests/opencode-int-test/container-test-opencode.sh --down
```

Os testes usam BATS-core com bibliotecas versionadas no próprio repo em
`tests/bats-libs/`.

Documentação do framework: [BATS-core](https://bats-core.readthedocs.io/)

Pre-requisitos:

- `make`
- dependencias externas conforme o alvo escolhido
- Docker para a Camada 2 (`make test-opencode-integration`)
