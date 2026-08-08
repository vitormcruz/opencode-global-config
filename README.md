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

O bootstrap detecta e instala dependencias com `opencode-bootstrap`. Em
WSL/Linux ele configura o OpenCode; no Windows configura somente o Copilot CLI.
Use `--yes`, `--quiet` ou `--check-only` conforme a necessidade.

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

Detectadas e instaladas automaticamente pelo `opencode-bootstrap`, sempre em
user-space:

- Python >= 3.10
- Node.js via fnm
- `pipx`
- `crawl4ai` (`crwl`) e o browser via `crawl4ai-setup`
- `docling`
- `codebase-memory-mcp`
- pandoc portatil
- PortableGit no Windows
- Playwright + Chromium
- pytest e plugins em `.venv`
- `aws-cli` v2 (dependencia obrigatoria gerenciada pelo bootstrap)

O AWS CLI v2 e usado por `aws-sso-login` e `aws-add-account-sso`.

Para rodar so a verificacao de dependencias:

```bash
./scripts/bootstrap_repo/configurar-repo.sh --check-only
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
opencode-adapter --yes
opencode-copilot-adapter --yes
```

O mesmo comando Python funciona no Linux, WSL e Windows.

Destinos sincronizados pelo Copilot CLI:

- `agents/*.md` → `~/.copilot/agents/*.agent.md`
- `commands/*.md` → `~/.copilot/skills/*/SKILL.md`
- `skills/*/` → `~/.copilot/skills/`
- `agents/default-artifacts/` → `~/.copilot/agents/default-artifacts/`
- `.github/copilot-specific.instructions.md` → `~/.copilot/instructions/`

## Testes

Comandos disponiveis:

```bash
.venv/bin/pytest -m unit
.venv/bin/pytest -m tools
.venv/bin/pytest -m "unit or tools or opencode"
.venv/bin/pytest -m "unit or tools or copilot"
```

### Testes de integração (Camada 2)

Os testes de integração exigem um modelo configurado explicitamente. Por segurança,
**não há modelo padrão** — você deve escolher conscientemente qual modelo usar.

**Opção 1: modelo próprio (recomendado)**

```bash
export OPENCODE_TEST_MODEL='openai/gpt-4'
.venv/bin/pytest -m opencode
```

> **AVISO**: O modelo aberto padrão (`opencode/big-pickle`) é um modelo externo
> que **COLETA DADOS** enviados a ele. **Nunca use em ambientes corporativos ou
> com dados sensíveis.** Use apenas para testes pessoais ou de demonstração.

Para executar a integração Copilot:

```bash
.venv/bin/pytest -m copilot
```

Pre-requisitos:

- Python >= 3.10 e dependências de `requirements-dev.txt`
- Docker para a integração OpenCode
- `OPENCODE_TEST_MODEL` para testes que enviam prompts
- dependencias externas conforme o alvo escolhido
