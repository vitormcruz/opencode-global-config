# opencode-config

Repo com as configuracoes globais do OpenCode para este usuario/maquina.

## Como funciona

- O OpenCode le as configuracoes globais a partir de `~/.config/opencode`.
- Este repo e a fonte de verdade e pode ficar em qualquer caminho local.
- O bootstrap cria links simbolicos em `~/.config/opencode` apontando para este repo.

## Bootstrap

Depois de clonar este repo, rode:

```bash
./scripts/opencode-link
```

No ambiente WSL deste repo, o script faz duas coisas:

- cria/atualiza os links simbolicos em `~/.config/opencode`
- garante `export OPENCODE_ENABLE_EXA=1` em `~/.bashrc`

Para aplicar a variavel no shell atual depois do bootstrap:

```bash
source ~/.bashrc
```

## O que o script faz

O `scripts/opencode-link` conecta estes caminhos:

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

O bootstrap (`opencode-link`) chama automaticamente `scripts/opencode-install-deps`

### Dependencias instaladas manualmente (nao gerenciadas pelo bootstrap)

- **`resvg` ou `rsvg-convert`** — skill `svg-to-image` (conversao SVG → PNG)
  - Ubuntu/WSL: `sudo apt-get install -y librsvg2-bin` (instala `rsvg-convert`)
  - Alternativa mais fiel: [resvg releases](https://github.com/RazrFalcon/resvg/releases)

- **AWS CLI v2** — skills `aws-sso-login` e `aws-add-account-sso`
  - Instrucoes: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

Para rodar so a verificacao de dependencias:

```bash
./scripts/opencode-install-deps
```

## Testes

Os testes usam BATS-core com bibliotecas versionadas no proprio repo em
`tests/bats-libs/`.

Pre-requisitos:

- `make`
- dependencias externas conforme o alvo escolhido
- Docker para a Camada 2 (`make test-behavioral`)

Alvos disponiveis:

```bash
make help
make test
make test-unit
make test-integration
make test-smoke
make test-bootstrap
make test-behavioral
make test-infra
```

Resumo dos alvos:

- `make test`: roda a Camada 1 (sem Docker)
- `make test-unit`: estrutura estatica
- `make test-integration`: wrappers que dependem de ferramentas externas
- `make test-smoke`: smoke test E2E da Camada 1
- `make test-bootstrap`: testes do bootstrap
- `make test-behavioral`: Camada 2 via API HTTP do OpenCode
- `make test-infra`: valida a infra minima do BATS

Para a Camada 2, crie ou reutilize o container de testes com:

```bash
bash tests/setup-container.sh
```

Esse script faz o setup interativo do container e salva apenas configuracao em
`tests/.test-env`. A API key real nao e salva em arquivo.