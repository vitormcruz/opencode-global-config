# opencode-config

Repo com as configuracoes globais do OpenCode para este usuario/maquina.

## Como funciona

- Este repo e a fonte de verdade das configuracoes globais dos harnesses
  (OpenCode, Copilot CLI) e pode ficar em qualquer caminho local.
- No Linux/WSL, o OpenCode le as configuracoes globais a partir de
  `~/.config/opencode`.
- No Windows, o OpenCode recebe copia sincronizada em
  `%USERPROFILE%\.config\opencode`.
- O Copilot CLI recebe copia sincronizada em `~/.copilot` /
  `%USERPROFILE%\.copilot` em todos os sistemas.

## Estrutura do repositório

O que é copiado/sincronizado para os harnesses (OpenCode, Copilot CLI)
vive em `harness-conf/`:

- `harness-conf/agents/` — definições de agentes (+ `default-artifacts/`
  e `references/`)
- `harness-conf/skills/` — skills (locais e importadas de upstream)
- `harness-conf/commands/` — comandos
- `harness-conf/opencode.json` — configuração do OpenCode
- `harness-conf/AGENTS.base.md` — regras globais para todos os harnesses

A infraestrutura do próprio repo fica na raiz: `scripts/`, `src/`,
`tests/`, `docs/`, `adapters/`, `plan/`, `README.md` e o `AGENTS.md`
(regras específicas deste repo, que complementam a base).

## Bootstrap

Depois de clonar este repositório, use o entrypoint correspondente ao sistema
operacional:

```bash
./scripts/bootstrap_repo/configurar-repo.sh --yes
```

```powershell
.\scripts\bootstrap_repo\configurar-repo.ps1 --yes
```

O bootstrap verifica Python >= 3.10, detecta as dependências e configura
todos os harnesses instalados no sistema corrente (OpenCode e Copilot CLI);
harness ausente no PATH é ignorado com aviso. A flag `--harness a,b`
restringe a subconjunto (ex.: `--harness copilot`). A instalação é sempre
em user-space; não usa `sudo` nem exige administrador. Use `--yes`,
`--quiet` ou `--check-only` conforme a necessidade.

`--check-only` apenas detecta dependências e exibe os comandos manuais
pendentes. Não instala, não executa adapters e não altera configurações.

No Linux/WSL, o OpenCode usa links simbólicos em `~/.config/opencode` e o
adapter garante `OPENCODE_ENABLE_EXA=1` no `~/.bashrc`. Para aplicar a
variável no shell atual:

```bash
source ~/.bashrc
```

No Windows, o OpenCode recebe cópia sincronizada em
`%USERPROFILE%\.config\opencode` e `OPENCODE_ENABLE_EXA` é persistida em
`HKCU\Environment` com broadcast de `WM_SETTINGCHANGE` — novos processos
enxergam a variável sem logoff. O Copilot CLI recebe cópia sincronizada em
`%USERPROFILE%\.copilot` em qualquer sistema.

## O que o script faz

No Linux/WSL, o `configurar-repo.sh` cria links simbolicos em
`~/.config/opencode`:

- `~/.config/opencode/agents` -> `harness-conf/agents`
- `~/.config/opencode/commands` -> `harness-conf/commands`
- `~/.config/opencode/opencode.json` -> `harness-conf/opencode.json`
- `~/.config/opencode/skills` -> `harness-conf/skills`
- `~/.config/opencode/scripts` -> `scripts` (infra do repo, fica na raiz)

O `~/.config/opencode/AGENTS.md` e um arquivo regular gerado pelo
adapter: conteudo de `harness-conf/AGENTS.base.md` + blocos gerenciados
por ferramentas de terceiros (como o codebase-memory-mcp), que sao
preservados entre execucoes. Nunca e symlink e nunca deve ser editado a
mao.
O arquivo base também orienta a leitura por trechos, a redução do contexto
e a execução paralela de chamadas independentes.

Se ja existir algo nesses destinos, o script move o conteudo anterior para um
backup em `~/.config/opencode-backup/<timestamp>` antes de recriar os links.

No Windows, os quatro destinos de `harness-conf/` (agents, commands, skills,
`opencode.json`) sao materializados como copia sincronizada em
`%USERPROFILE%\.config\opencode` a cada execucao do bootstrap, com backup do
conteudo divergente. Divergencias entre execucoes sao realinhadas no proximo
sync.

### ai-memory

O bootstrap provisiona o ai-memory em user-space quando Docker está
disponível. O wrapper vem de um release oficial do GitHub e passa por
validação SHA-256 fixada no código. A imagem continua em `:latest`, conforme
decisão do produto. O container publica apenas `127.0.0.1:49374` e usa uma
rede Docker `internal`, sem rota de saída padrão.

O volume fica em `~/.local/share/ai-memory/`. A wiki contém prompts em texto
claro. Trate o diretório como dado sensível: não o versione nem o sincronize
para um destino compartilhado. No POSIX, o bootstrap restringe o diretório ao
usuário. O bootstrap não instala chaves de LLM.

Depois de provisionar o container, o bootstrap executa `ai-memory install-hooks`
para gerar o plugin OpenCode. O plugin é artefato local regenerável e não é
versionado. O Copilot recebe somente a declaração MCP; os hooks de compactação
continuam limitados ao OpenCode.

O bootstrap não substitui um wrapper com checksum divergente. A mensagem de
erro informa o caminho para backup e remoção explícita antes de reexecutar.
Container antigo com mount incompatível também bloqueia a injeção. Confira o
mount de `/data` e faça uma cópia dos dados antes de reverter essa instalação.

Sem Docker, o bootstrap avisa e orienta a instalação de um runtime em user-space,
sem `sudo`. O bootstrap não declara `mcp.ai-memory` em nenhum harness. Em Linux,
use Docker rootless. No WSL, use Docker Desktop com integração WSL. Consulte
<https://docs.docker.com/engine/security/rootless/> ou
<https://docs.docker.com/desktop/setup/install/>. Depois de iniciar o runtime,
execute o bootstrap novamente.

No Linux/WSL, o adapter mantém `opencode.json` como symlink canônico quando o
provisionamento termina. Enquanto o ai-memory estiver desabilitado, o adapter
substitui o symlink por uma cópia filtrada que não declara esse MCP. Após um
provisionamento completo, a próxima execução restaura o symlink canônico. No
Copilot, o adapter mescla `mcpServers.ai-memory` e preserva as demais entradas.
O adapter cria backup antes de alterar `~/.copilot/mcp-config.json`.

O bootstrap move `~/.config/opencode/opencode.jsonc` para
`~/.config/opencode-backup/<timestamp>/opencode.jsonc`, sem editar o conteúdo.

Para reverter a integração, execute:

```bash
opencode-bootstrap --rollback-ai-memory
```

O rollback para e remove o container e a rede internal criada pelo bootstrap.
O rollback faz backup e remove hooks e wrappers gerenciados, remove declarações
MCP e restaura o backup de `opencode.jsonc`. O rollback preserva
`~/.local/share/ai-memory/`. A remoção do volume é uma ação separada do usuário.

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

## Plugins

- `@slkiser/opencode-quota`: quota de tokens no toast/TUI.
- `opencode-task-model@1.3.1` (PROVISÓRIO): adiciona `model`, `reasoning`,
  `background` e `worktree` por chamada na tool `task`. Instalado porque o
  OpenCode nativo ainda não aceita modelo no spawn (rastreio: PR
  anomalyco/opencode#34947, issue #6651). Remover quando a versão nativa
  suportar `model` na task; o pin é atualizado manualmente com
  `npm view opencode-task-model version`, sempre precedido de nova revisão
  de segurança registrada em
  `harness-conf/plugins/opencode-task-model/UPSTREAM.md`.

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
| codebase-memory-mcp 0.10.8 | npm com prefixo user-space | npm com prefixo user-space |
| pandoc | arquivo portátil oficial | arquivo portátil oficial |
| git | pré-existente ou pacote do sistema | PortableGit |
| Playwright + Chromium | npm + `npx playwright install` | igual ao Linux |
| pytest | `.venv` + `requirements-dev.txt` | igual ao Linux |
| AWS CLI v2 | instalador oficial user-local | instalador oficial user-local |
| `libgomp.so.1` | pacote Debian fixado, extraido no cache | nao aplicavel |
| entry points do repo | `pipx install --editable .` | igual ao Linux |
| Copilot CLI | npm com prefixo user-space | npm com prefixo user-space |
| ai-memory | Docker rootless; no WSL, Docker Desktop integrado | Docker Desktop em escopo do usuário |
| ruff | `pipx install ruff` | `pipx install ruff` |
| shellcheck | `pipx install shellcheck-py` | release oficial no cache user-space |
| pwsh | arquivo portatil em user-space | arquivo zip em user-space |
| PSScriptAnalyzer | `Install-Module -Scope CurrentUser` via pwsh | igual ao Linux |
| pytest-cov | `.venv` + `requirements-dev.txt` | igual ao Linux |
| gitleaks | release oficial no cache user-space | release oficial no cache user-space |
| pip-audit | `pipx install pip-audit` | `pipx install pip-audit` |
| bandit | `pipx install bandit` | `pipx install bandit` |
| JDK | OpenJDK portatil no cache user-space | OpenJDK portatil no cache user-space |
| Gradle | distribuicao portatil no cache user-space | distribuicao portatil no cache user-space |

`pytest` é opcional na seleção interativa, mas entra no conjunto instalado por
`--yes`. O AWS CLI v2 é obrigatório para `aws-analista`, `aws-sso-login` e
`aws-add-account-sso`; após o bootstrap, abra um novo PowerShell no Windows
para carregar o PATH persistido e confirme com `aws --version`.

As ferramentas do `testes-produto` entram no conjunto do bootstrap com `--yes`.
O WSL/Linux recebe `pwsh` para executar o PSScriptAnalyzer. O Windows recebe
`shellcheck` para analisar os scripts Bash. O JDK e o Gradle ficam no cache
user-space e executam as specs Concordion sem instalação global.

Comandos manuais equivalentes, todos sem elevação:

```bash
pipx install ruff
pipx install shellcheck-py
pipx install pip-audit
pipx install bandit
```

No Windows, o bootstrap baixa o zip oficial do ShellCheck para o cache do
usuário e adiciona o executável ao PATH do usuário.

No PowerShell, o PSScriptAnalyzer usa o escopo do usuário:

```powershell
pwsh -NoProfile -Command "Install-Module PSScriptAnalyzer -Scope CurrentUser -Force"
```

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

O repositório mantém uma fonte canônica e adapters de harness multi-SO,
orquestrados pelo bootstrap via factory:

| Adapter | Entrada | Destino |
|---|---|---|
| `opencode-adapter` | agents, skills, commands e configuração | Linux/WSL: `~/.config/opencode/` |
|  |  | Windows: `%USERPROFILE%\.config\opencode` |
| `harnesses/copilot.py` (`opencode-copilot-adapter`) | fonte canônica transformada | `~/.copilot/` |

No Linux/WSL o adapter OpenCode cria links simbólicos. No Windows usa cópia
sincronizada e persiste env vars de usuário em `HKCU\Environment` com
broadcast de `WM_SETTINGCHANGE`. O adapter Copilot CLI converte frontmatter
de agentes, transforma commands em skills, valida skills no padrão
agentskills.io e copia artefatos auxiliares, em qualquer sistema.

Use diretamente:

```bash
opencode-adapter --yes
opencode-copilot-adapter --yes
```

Os dois comandos funcionam em Linux, WSL e Windows; cada adapter configura
seu harness no formato do sistema corrente. O bootstrap executa ambos
automaticamente quando os harnesses estão instalados.

O adapter OpenCode não altera arquivos da fonte canônica. Para revisar mudanças
sem alterar skills, execute `opencode-skills detect FAMÍLIA`. Depois da decisão
humana e das edições aprovadas, sincronize com `opencode-skills sync FAMÍLIA`.

Destinos sincronizados pelo Copilot CLI:

- `harness-conf/agents/*.md` → `~/.copilot/agents/*.agent.md`
- `harness-conf/commands/*.md` → `~/.copilot/skills/*/SKILL.md`
- `harness-conf/skills/*/` sem deny global em `harness-conf/opencode.json`
  → `~/.copilot/skills/` (10 skills globais no mapa atual)
- `harness-conf/skills/*/` cobertas por deny global no mesmo mapa
  → `~/.copilot/referencias/skills/` (23 skills de domínio no mapa atual),
  fora da descoberta automática
- `harness-conf/agents/default-artifacts/` →
  `~/.copilot/agents/default-artifacts/`
- `harness-conf/AGENTS.base.md` → `~/.copilot/AGENTS.md`

A classificação usa as regras `permission.skill` globais, inclusive wildcards.
Na sincronização, o adapter faz backup e remove cópias antigas do destino
incorreto para evitar descoberta de skills de domínio.
Perfis materializados recebem referências completas e caminhos absolutos apenas
para as skills de domínio autorizadas em cada agente.

## Testes

Taxonomia de markers agnóstica de SO e harness (detalhes em
`docs/adr/0005-taxonomia-testes.md`):

```bash
.venv/bin/pytest -m unit          # sem premissas externas
.venv/bin/pytest -m integration   # ferramenta no PATH, binario de harness, Docker, capacidade do SO
.venv/bin/pytest -m all           # atalho traduzido para unit or integration
.venv/bin/pytest -m agent_eval    # avaliacao de agente com modelo local (demorada)
```

`-m all` é tradução literal de atalho feita pelo conftest antes da seleção;
nunca inclui `agent_eval` e não acrescenta nem remove nada além do token
`all`. Teste que exige capacidade de SO declara `skipif` no próprio teste
(ex.: "exige symlink (POSIX)"): a suíte não o executa onde a capacidade não
se aplica e o relatório mostra o skip com o motivo.

No Windows, use o executável da virtualenv pelo PowerShell:

```powershell
.\.venv\Scripts\pytest.exe -m all
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

O único comando da avaliação de agente (OpenCode + Qwen local) é:

```bash
.venv/bin/pytest -m agent_eval
```

O Qwen usa o artefato fixado `Qwen3-0.6B-Q8_0.gguf` do repositório
`Qwen/Qwen3-0.6B-GGUF`; o harness valida o SHA-256 antes de iniciar o servidor.
Depois do provisionamento, a execução usa o cache local e permanece offline,
sem telemetria, egress ou handoff em cloud.

Ao iniciar a suíte, a fixture session-scoped reutiliza o `llama-server` e sobe
o container OpenCode na porta local `127.0.0.1:4196`. A rede dedicada valida
`Internal=true` e calcula o gateway real antes de criar
`host.docker.internal`, sem aceitar overlays externos de configuração.

A suíte do Copilot CLI faz parte de `-m integration` (o binário `copilot` é
a premissa externa declarada pelo próprio teste).

Pré-requisitos:

- Python >= 3.10 e dependências de `requirements-dev.txt`
- Docker somente para `-m agent_eval` no WSL/Linux
- acesso ao pacote libgomp fixado, ao release Prism e aos pesos Qwen para o
  primeiro provisionamento local
- dependências externas conforme o alvo escolhido

O build da imagem Docker tem acesso à rede apenas para instalar o OpenCode.
Durante os testes, o container usa a rede interna `opencode-test-net`, sem rota
para a internet, e acessa somente o llama-server pelo gateway real da bridge.
