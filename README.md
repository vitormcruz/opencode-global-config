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

- `~/.config/opencode/AGENTS.md` -> `AGENTS.md`
- `~/.config/opencode/agents` -> `agents`
- `~/.config/opencode/commands` -> `commands`
- `~/.config/opencode/opencode.json` -> `opencode.json`
- `~/.config/opencode/skills` -> `skills`
- `~/.config/opencode/scripts` -> `scripts`

Se ja existir algo nesses destinos, o script move o conteudo anterior para um backup em `~/.config/opencode-backup/<timestamp>` antes de recriar os links.

## Variaveis de ambiente

- `OPENCODE_ENABLE_EXA=1`: habilita a tool `websearch` do OpenCode via Exa AI

Sem essa variavel, a tool `websearch` nao aparece no runtime quando o provider nao e o nativo do OpenCode.

## Dependencias das skills

O bootstrap (`opencode-link`) chama automaticamente `scripts/opencode-install-deps`, que:

- **Instala automaticamente** (user-space, sem sudo):
  - `docling` via `pipx` (skill `doc-extract`)
  - `pipx` via `pip --user` se necessario

- **Sugere o comando** para instalar via sudo (nao executa sozinho):
  - `pandoc` — skill `md-export`
  - `tesseract-ocr`, `ocrmypdf`, `ghostscript`, `qpdf` — OCR opcional para PDFs

Para instalar as dependencias que precisam de sudo (Ubuntu/WSL):

```bash
sudo apt-get update && sudo apt-get install -y pandoc pipx tesseract-ocr ocrmypdf ghostscript qpdf
```

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

## Estrutura do repo

- `AGENTS.md`: instrucoes globais carregadas pelo OpenCode
- `agents/`: agentes customizados
- `commands/`: comandos customizados do OpenCode
- `opencode.json`: configuracao principal do OpenCode e MCPs
- `skills/`: skills no formato canonico `skills/<nome>/SKILL.md`
  - `skills/md-export/`: converte Markdown para docx/pptx/xlsx via Pandoc
  - `skills/doc-extract/`: extrai conteudo de PDF/docx/imagens via Docling
  - `skills/svg-to-image/`: converte SVG em PNG para exibir ao usuario
  - `skills/aws-sso-login/`: valida/renova sessao AWS SSO para um profile
  - `skills/aws-add-account-sso/`: adiciona novos perfis AWS SSO no ~/.aws/config
  - `skills/web-research-exa-crawl4ai/`: pesquisa web hibrida (Exa + Crawl4AI)
  - `skills/prompt-improver/`: melhora e estrutura prompts
- `scripts/`: utilitarios e bootstrap local
  - `scripts/opencode-link`: bootstrap principal (cria symlinks)
  - `scripts/opencode-install-deps`: verifica e instala dependencias das skills
  - `scripts/opencode-md-export`: script da skill md-export
  - `scripts/opencode-doc-extract`: script da skill doc-extract
  - `scripts/opencode-svgtoimage`: script da skill svg-to-image
