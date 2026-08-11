# opencode-config

Repo com as configuracoes globais do OpenCode para este usuario/maquina.

## Como funciona

- No Linux/WSL, o OpenCode le as configuracoes globais a partir de
  `~/.config/opencode`.
- Este repo e a fonte de verdade e pode ficar em qualquer caminho local.
- No Windows, o bootstrap copia os artefatos para
  `%USERPROFILE%\.copilot`.

## Bootstrap

Depois de clonar este repositório, use o entrypoint correspondente ao sistema
operacional:

```bash
./scripts/bootstrap_repo/configurar-repo.sh --yes
```

```powershell
.\scripts\bootstrap_repo\configurar-repo.ps1 --yes
```

O bootstrap verifica Python >= 3.10, detecta as dependências e configura o
adapter correto: OpenCode no Linux/WSL e Copilot CLI no Windows. A instalação
é sempre em user-space; não usa `sudo` nem exige administrador. Use
`--yes`, `--quiet` ou `--check-only` conforme a necessidade.

`--check-only` apenas detecta dependências e exibe os comandos manuais
pendentes. Não instala, não executa adapters e não altera configurações.

No Linux/WSL, o adapter cria links simbólicos em `~/.config/opencode` e
garante `OPENCODE_ENABLE_EXA=1` no `~/.bashrc`. Para aplicar a variável no
shell atual:

```bash
source ~/.bashrc
```

No Windows, o adapter copia os artefatos para `%USERPROFILE%\.copilot` e não
configura o OpenCode.

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

## Dependências

Python >= 3.10 é o único pré-requisito do entrypoint e deve estar disponível
antes do bootstrap. As demais dependências são detectadas e instaladas em
user-space conforme a seleção interativa ou `--yes`:

| Dependência | Linux/WSL | Windows |
|---|---|---|
| Node.js 22 + npm/npx | fnm portátil | fnm portátil |
| pipx | `pip install --user pipx` | `py -m pip install --user pipx` |
| `crwl` | `pipx install crawl4ai` + `crawl4ai-setup` | igual ao Linux |
| docling | `pipx install docling` | igual ao Linux |
| codebase-memory-mcp 0.9.0 | npm com prefixo user-space | npm com prefixo user-space |
| pandoc | arquivo portátil oficial | arquivo portátil oficial |
| git | pré-existente ou pacote do sistema | PortableGit |
| Playwright + Chromium | npm + `npx playwright install` | igual ao Linux |
| pytest | `.venv` + `requirements-dev.txt` | igual ao Linux |
| AWS CLI v2 | instalador oficial user-local | instalador oficial user-local |
| entry points do repo | `pipx install --editable .` | igual ao Linux |
| Copilot CLI | cliente externo | npm com prefixo user-space |

`pytest` é opcional na seleção interativa, mas entra no conjunto instalado por
`--yes`. O AWS CLI v2 é obrigatório para `aws-analista`, `aws-sso-login` e
`aws-add-account-sso`; após o bootstrap, abra um novo PowerShell no Windows
para carregar o PATH persistido e confirme com `aws --version`.

Em redes corporativas, o download dos browsers do Playwright/Patchright pode
usar um mirror configurado apenas no ambiente, sem URL fixa no repositório:

```powershell
$env:PLAYWRIGHT_DOWNLOAD_HOST = "https://<mirror-corporativo>/playwright"
```

No Linux/WSL, use `export PLAYWRIGHT_DOWNLOAD_HOST=...`. Sem essa variável, o
bootstrap usa o CDN público padrão do Playwright.

Falhas de certificado ou TLS aparecem no bloco de comandos pendentes com
orientação para o agente conversar com o humano sobre uma CA PEM aprovada ou
mirror do ambiente. O bootstrap não desativa TLS nem grava certificados.

Os comandos `opencode-doc-extract`, `opencode-md-export`,
`opencode-svgtoimage` e `opencode-browser-test` são instalados pelo próprio
bootstrap via `pipx install --editable .`.

O Docling não exige um modelo LLM externo para ser instalado ou executado pelo
wrapper. O wrapper executa em modo offline: modelos precisam existir no cache
local; downloads e telemetria ficam desativados. A conversão PDF pode exigir
artefatos locais de layout/OCR previamente provisionados.

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

Linux/WSL:

```bash
opencode-adapter --yes
```

Windows:

```powershell
opencode-copilot-adapter --yes
```

O pacote Python é compartilhado entre os sistemas, mas cada adapter respeita
seu cliente: `opencode-adapter` é exclusivo de Linux/WSL e
`opencode-copilot-adapter` é o adapter do Windows.

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

No Windows, use o executável da virtualenv pelo PowerShell:

```powershell
.\.venv\Scripts\pytest.exe -m "unit or tools or copilot"
```

### Testes de integração (Camada 2)

Os testes de integração exigem um modelo configurado explicitamente. Por
segurança, **não há modelo padrão** — você deve escolher conscientemente qual
modelo usar.

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

Pré-requisitos:

- Python >= 3.10 e dependências de `requirements-dev.txt`
- Docker somente para a integração OpenCode no WSL/Linux
- `OPENCODE_TEST_MODEL` para testes que enviam prompts
- dependências externas conforme o alvo escolhido
