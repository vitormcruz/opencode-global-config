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

- `OPENCODE_CONFIG_REPO`: substitui a detecção automática da raiz do checkout;
  use apenas quando o repo estiver em um caminho não detectável.
- `OPENCODE_ENABLE_EXA=1`: habilita a tool `websearch` do OpenCode via Exa AI

Sem essa variavel, a tool `websearch` nao aparece no runtime quando o provider nao e o nativo do OpenCode.

### Variáveis de validação

Estas variáveis existem apenas para diagnósticos controlados e testes do
bootstrap; uma execução completa não deve usá-las:

- `OPENCODE_SKIP_DEPS=1`: não instala nem detecta dependências.
- `OPENCODE_SKIP_OPENCODE_ADAPTER=1`: não executa o adapter OpenCode.
- `OPENCODE_SKIP_COPILOT_ADAPTER=1`: não executa o adapter Copilot CLI.

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
| `libgomp.so.1` | pacote Debian fixado, extraido no cache | nao aplicavel |
| entry points do repo | `pipx install --editable .` | igual ao Linux |
| Copilot CLI | cliente externo | npm com prefixo user-space |

`pytest` é opcional na seleção interativa, mas entra no conjunto instalado por
`--yes`. O AWS CLI v2 é obrigatório para `aws-analista`, `aws-sso-login` e
`aws-add-account-sso`; após o bootstrap, abra um novo PowerShell no Windows
para carregar o PATH persistido e confirme com `aws --version`.

No Linux/WSL o instalador oficial do AWS CLI v2 exige `unzip` (pacote do
sistema), que não pode ser instalado em user-space. O bootstrap detecta a
ausência e falha com a instrução clara antes de baixar o bundle. Instale com:

```bash
sudo apt install unzip   # ou o equivalente da sua distro
```

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
Uma extração só é considerada bem-sucedida quando o Docling gera pelo menos um
artefato não vazio; documentos sem conteúdo retornam erro explícito.

Ao finalizar o bootstrap com Docling disponível, o terminal imprime o comando
de provisionamento local. O download é opcional e deve ser executado pelo
humano em sessão aprovada; `--check-only` não imprime nem executa esse comando.

Para rodar so a verificacao de dependencias:

```bash
./scripts/bootstrap_repo/configurar-repo.sh --check-only
```

## Adapters

O repositório mantém uma fonte canônica e adapters por plataforma:

| Adapter | Entrada | Destino |
|---|---|---|
| `adapters/opencode/` | agents, skills, commands e configuração | links em `~/.config/opencode/` |
| `src/opencode_config/adapters/copilot.py` | fonte canônica transformada | `~/.copilot/` |

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

O adapter OpenCode não altera arquivos da fonte canônica. A sincronização de
skills upstream é uma operação separada: `opencode-skills sync NOME`.

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

Os testes comportamentais do OpenCode usam exclusivamente o Qwen3-0.6B Q8_0,
servido pelo llama-server no WSL/Linux. O harness provisiona os artefatos no
cache do usuário quando necessário e reutiliza somente artefatos verificados.
Consulte a seção de pré-requisitos antes de executar a suíte.

#### Servidor local Qwen3-0.6B

O servidor requer aproximadamente 1 GB livre em
`~/.cache/opencode-config/models/`. O harness baixa automaticamente o binário
self-contained do release fixado `prism-b9596-9fcaed7` para
`~/.cache/opencode-config/llama/` e o modelo
`Qwen3-0.6B-Q8_0.gguf` para o cache de modelos. Não é necessário instalar
`llama-server` no `PATH` nem baixar um projector: a linha de comando não usa
`--mmproj`.

O Prism precisa de `libgomp.so.1`. No Linux/WSL, o bootstrap provisiona uma
copia autocontida em
`~/.cache/opencode-config/runtime/libgomp/12.2.0-14+deb12u1-amd64/`, sem
`sudo`, `apt`, instalacao global ou `LD_LIBRARY_PATH`. A origem e o artefato
sao fixados:

- pacote oficial Debian Snapshot:
  `libgomp1_12.2.0-14+deb12u1_amd64.deb`;
- URL:
  `https://snapshot.debian.org/archive/debian/20250415T084322Z/pool/main/g/`
  `gcc-12/libgomp1_12.2.0-14%2Bdeb12u1_amd64.deb`;
- SHA-256 do pacote:
  `48fec46bda7f5b1638b9e959889bfbc20491247d402d120bb152687eb48143d7`;
- SHA-256 de `libgomp.so.1.0.0`:
  `f9a9ad78a8dc39c0e90a265ffa551fae6c92a40f360889b44a7e141f9a2adfb1`;
- arquitetura: `amd64`/Linux x86_64; licença: GPLv3-or-later com GCC Runtime
  Library Exception 3.1.

O bootstrap valida pacote, metadados, checksum e carregamento ELF. O servidor
inicia o Prism pelo interpretador ELF `ld-linux-x86-64.so.2`, usando
`--library-path` para os caches do Prism/libgomp e as bibliotecas do sistema;
não altera variaveis globais. A redistribuicao deve manter os avisos GPLv3 e a
Runtime Library Exception e preservar a origem fixada. Depois do bootstrap, o
servidor e os testes reutilizam o cache e permanecem offline.

```bash
python3 tests/integration/model/local_model_server.py --up
python3 tests/integration/model/local_model_server.py --status
```

O processo usa `--jinja` para tool calling e
`--sleep-idle-seconds 600`: após 10 minutos sem requisições, os pesos saem da
memória e são recarregados automaticamente na próxima requisição. A fixture
pytest reaproveita o processo e não o encerra. Para desligamento explícito:

```bash
python3 tests/integration/model/local_model_server.py --down
```

O único comando de integração OpenCode é:

```bash
.venv/bin/pytest -m opencode
```

O Qwen usa o artefato fixado `Qwen3-0.6B-Q8_0.gguf` do repositório
`Qwen/Qwen3-0.6B-GGUF`; o harness valida o SHA-256 antes de iniciar o servidor.
Depois do provisionamento, a execução usa o cache local e permanece offline,
sem telemetria, egress ou handoff em cloud.

Ao iniciar a suíte, a fixture session-scoped reutiliza o `llama-server` e sobe
o container OpenCode na porta local `127.0.0.1:4196`. A rede dedicada valida
`Internal=true` e calcula o gateway real antes de criar
`host.docker.internal`, sem aceitar overlays externos de configuração.

Para executar a integração Copilot:

```bash
.venv/bin/pytest -m copilot
```

Pré-requisitos:

- Python >= 3.10 e dependências de `requirements-dev.txt`
- Docker somente para a integração OpenCode no WSL/Linux
- acesso ao pacote libgomp fixado, ao release Prism e aos pesos Qwen para o
  primeiro provisionamento local
- dependências externas conforme o alvo escolhido

O build da imagem Docker tem acesso à rede apenas para instalar o OpenCode.
Durante os testes, o container usa a rede interna `opencode-test-net`, sem rota
para a internet, e acessa somente o llama-server pelo gateway real da bridge.
