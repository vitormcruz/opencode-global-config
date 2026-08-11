# Implementation Plan: Migração de MCPs para Ferramentas CLI (WSL + Windows)

## Overview

Eliminar completamente o uso de servidores MCP locais, substituindo-os por
ferramentas CLI equivalentes, e dar paridade real entre WSL/Linux e Windows.

O levantamento mostrou que o pedido original (remover MCP) não é separável de
três problemas estruturais adjacentes, e por isso todos entram no escopo:

1. **MCP → CLI.** `crawl4ai` deixa de rodar em container Docker e passa a usar
   o CLI `crwl`; `codebase-memory` passa a usar seu CLI nativo. O wrapper
   `avelino/mcp` é removido.
2. **Bash/PowerShell → Python.** O repo mantém hoje pares `.sh`/`.ps1` que
   precisam ser sincronizados manualmente, e o adapter Windows contorna a
   diferença reescrevendo comandos para `wsl bash` — o oposto de paridade.
   Todo o código vira um pacote Python instalável, com dois entrypoints shell
   apenas para resolver o ovo-e-galinha do bootstrap.
3. **BATS → pytest.** BATS não roda no Windows, onde a suíte do Copilot
   passará a rodar.

Ao final: nenhum MCP local, nenhum Docker para crawl4ai, um só runner de
teste, um só código-fonte por ferramenta, e instalação sem privilégio de
administrador nos dois SOs.

**Escopo:** 12 decisões de arquitetura, 28 tasks em 7 fases, ~3.500 linhas de
shell e 4.608 linhas de BATS migradas.

## Tracking de execução

**Estado atual:** Tasks 6.1 e 6.2 concluídas no WSL. A implementação e a
revisão documental da Task 6.3 foram concluídas. A validação Windows da Task
4.5 foi executada e registrada como PASS pelo agente Windows; a revisão humana
permanece pendente. Os defeitos Windows
anteriores de PATH case-insensitive, instalação do pacote no `.venv`, caminho
real de apps do pipx e detecção independente de `npm`/`npx` foram cobertos por
testes e corrigidos. O wrapper Docling agora usa a sintaxe comum às versões
verificadas e rejeita artefatos vazios; a validação nativa Windows foi repetida
com sucesso.

**Concluído:** Fase 0, Fase 1, Tasks 2.1–2.4, Tasks 3.1–3.2, Tasks 4.1–4.4,
Tasks 5.1–5.3 e Tasks 6.1–6.2.

**Exceção registrada:** a integração OpenCode continua bloqueada sem
`OPENCODE_TEST_MODEL`, conforme decisão explícita do humano. Esse bloqueio não
impediu a execução das demais verificações no WSL.

**Diretriz de validação:** todas as verificações que exigem Windows serão
executadas somente ao final da migração, pelo humano, em outra instalação.
Essas pendências não bloqueiam a execução das fases intermediárias.

**Última verificação WSL:** após os commits Windows, a suíte
`.venv/bin/pytest -m "unit or tools" -q` terminou com `372 passed, 46
deselected` após a correção do contrato Docling e do teste auxiliar
multiplataforma. No Windows, `pytest -m "unit or tools or copilot" -q`
terminou com `374 passed, 44 deselected`.
Para a Task 5.1, `pytest -m unit tests/skills_mgmt/test_sync.py` passou com
25 testes.
Para a Task 5.2, `pytest -m unit tests/skills_mgmt/test_update.py` passou com
23 testes.
Para a Task 5.3, `pytest -m unit tests/scaffold/test_mapa_produto.py` passou
com 30 testes, incluindo a comparação da árvore Bash versus Python.

## Contexto Levantado (inventário pré-migração)

### Estado atual

| Item | Onde | Situação |
|---|---|---|
| `mcp` (avelino) CLI | `scripts/bootstrap_repo/wsl-install-deps.sh:573+` | instala binário em `~/.local/bin/mcp` |
| `servers.json` (mcpServers) | adapters copilot-cli (`.sh:385+`, `.ps1:492+`) | escreve `~/.config/mcp/servers.json` |
| MCP crawl4ai | `opencode.json` (remote SSE `:11235/mcp/sse`) | container Docker `crawl4ai-sanitized` |
| MCP codebase-memory | `opencode.json` (local `codebase-memory-mcp`) | binário npm |
| Imagem sanitizada | `scripts/crawl4ai/docker/*` | patch só necessário para protocolo MCP |
| Skill web-research | `skills/web-research-exa-crawl4ai/SKILL.md` | referencia tools MCP `crawl4ai_md` etc. |
| Instruções Copilot | `.github/copilot-specific.instructions.md` | todo o doc gira em torno do wrapper `mcp` |
| Regras globais | `AGENTS.md` (linhas 5-50, 108-115) | idem |
| README | seção Dependências + Bootstrap | lista `mcp (avelino)` |
| Makefile | target `test-copilot-integration` | exige `mcp` no PATH |

### Descobertas técnicas

- `codebase-memory-mcp` **já possui CLI nativo**:
  `codebase-memory-mcp cli <tool> '<json>'` — o wrapper `avelino/mcp` é
  dispensável para este servidor.
- O container crawl4ai expõe **REST API completa**: `/md`, `/html`,
  `/screenshot`, `/pdf`, `/execute_js`, `/crawl`, `/health`, `/ask`.
  Um wrapper CLI via `curl` cobre todos os casos de uso da skill.
- A imagem `crawl4ai-sanitized` existe **apenas** para corrigir schemas do
  protocolo MCP. Ao migrar para REST, ela pode ser eliminada
  (usar `unclecode/crawl4ai:latest` direto).
- Não há bootstrap para Windows: só `configurar-repo.sh` (bash) e o
  `copilot-cli-adapter.ps1` avulso.
- O `.ps1` já faz substituição `websearch` -> `web_search_exa` no
  `Adapt-SkillForCopilot`; o `.sh` **não faz** (divergência entre adapters).

### Testes impactados

- `tests/scripts/bootstrap_repo/wsl-install-deps-test.bats` (7 testes `mcp-avelino:*`)
- `tests/integration/copilot-cli-test.bats` (smoke `mcp --list`)
- `tests/integration/copilot-mcp-test.bats` (arquivo inteiro)
- `tests/integration/mcp-test.bats`
- `tests/scripts/crawl4ai/*` (3 arquivos)
- `tests/scripts/codebase-memory/*` (2 arquivos)
- `tests/adapters/copilot-cli/*` (asserts sobre `servers.json`)
- `tests/scripts/bootstrap_repo/configurar-repo-test.bats`

## Architecture Decisions

### AD-1: Eliminar MCP por completo (opção A) — APROVADO

**Decisão:** zerar o bloco `mcp` do `opencode.json`. Nenhum servidor MCP local
permanece. OpenCode e Copilot consomem exclusivamente ferramentas CLI.

**Motivação (humano):** MCP local vem dando problemas recorrentes; objetivo é
simplificar ao máximo e ter paridade WSL/Windows.

**Consequências:**
- `codebase-memory` deixa de ser MCP → usa CLI nativo
  `codebase-memory-mcp cli <tool> '<json>'` (verificado, existe em v0.7.0).
- `crawl4ai` deixa de rodar em container Docker → usa CLI `crwl`
  (pacote PyPI `crawl4ai`, console script `crwl`, instalável via pipx).
- `~/.config/mcp/servers.json` deixa de ser gerado pelos adapters.
- Wrapper `avelino/mcp` é removido do bootstrap, docs e testes.
- Toda a árvore `scripts/crawl4ai/docker/` (Dockerfile, sanitize_mcp.py,
  sitecustomize.py, build.sh) é removida — existia só para o protocolo MCP.
- `scripts/crawl4ai/start-crawl4ai.sh` e o bloco de auto-start no `~/.bashrc`
  são removidos (não há mais container).

**Verificado sobre `crwl` (crawl4ai 0.9.2):**
- `crwl <url> -o markdown|md-fit|json|all` — extração principal
- `-c key=value` — params do crawler (`screenshot=true`, `pdf=true`, `js_code=...`)
- `-C/-B/-f/-e` — arquivos de config (crawler, browser, filtro, extração)
- `--deep-crawl bfs|dfs|best-first --max-pages N`
- `-q` — pergunta sobre o conteúdo; `crwl config`, `crwl profiles`, `crwl browser`
- Requer `crawl4ai-setup` pós-instalação (baixa browser Playwright)
- Python >= 3.10, 54 deps (inclui playwright/patchright)

### AD-2: Skills usam `crwl` direto, sem wrapper — APROVADO

**Decisão:** as skills invocam o binário `crwl` diretamente com suas flags
nativas. Nenhum wrapper `.sh`/`.ps1`/`.py` é criado.

**Motivação:** `crwl` é o mesmo comando em WSL e Windows (pipx expõe no PATH),
então um wrapper não resolveria portabilidade — só criaria dois arquivos
divergentes para manter em sincronia e testar.

**Mapeamento tool MCP → comando CLI:**

| Tool MCP antiga | Comando `crwl` |
|---|---|
| `crawl4ai_md` | `crwl <url> -o md-fit` (ou `-o markdown` para raw) |
| `crawl4ai_html` | `crwl <url> -o json` (campo `html`/`cleaned_html`) |
| `crawl4ai_execute_js` | `crwl <url> -c js_code="..." -o md-fit` |
| `crawl4ai_screenshot` | `crwl <url> -c screenshot=true -O saida.json` |
| `crawl4ai_pdf` | `crwl <url> -c pdf=true -O saida.json` |
| (novo) deep crawl | `crwl <url> --deep-crawl bfs --max-pages N` |

**Consequência:** a skill `web-research-exa-crawl4ai` deve trazer exemplos
prontos de cada caso, já que a sintaxe de screenshot/pdf é menos óbvia que a
das tools MCP.

### AD-3: Instalação nativa dupla (WSL/Linux e Windows) — APROVADO

**Decisão:** cada ambiente é autossuficiente. `crwl` e `codebase-memory-mcp`
são instalados nativamente também no Windows (pipx + npm nativos). O Copilot no
Windows invoca os binários direto, **sem** prefixo `wsl`.

**Motivação:** paridade real WSL/Windows. Delegar ao WSL mantém o Windows
dependente e traz dor de tradução de paths (`C:\` ↔ `/mnt/c`), escaping de
JSON em aspas e necessidade de `wsl -- bash -ic` para carregar PATH.

**Consequências:**
- Novo bootstrap Windows (PowerShell) espelhando `configurar-repo.sh` e
  `wsl-install-deps.sh`.
- `configurar-repo.sh` passa a detectar WSL vs Linux nativo e ajustar
  pacotes/paths.
- A reescrita `./scripts/X.sh` → `wsl bash <path>` no
  `copilot-cli-adapter.ps1` (`Rewrite-ScriptRefs`) deve ser eliminada — está
  em escopo deste plano (ver AD-4).

**Pré-requisitos no Windows:** Python >= 3.10 + pipx, Node.js + npm.

### AD-4: Todo o repo migra para Python; testes migram para pytest — APROVADO

**Decisão:** todos os scripts do repo passam a ser Python (fonte único,
cross-platform). BATS é eliminado e substituído por **pytest**.

**Motivação:** um só runner, um só ecossistema, execução nativa em Windows
(BATS não roda). Evita manter pares `.sh`/`.ps1` divergentes.

**Núcleo irredutível em shell (apenas 2 arquivos):**
- `scripts/bootstrap_repo/configurar-repo.sh` — entrypoint fino Linux/WSL
- `scripts/bootstrap_repo/configurar-repo.ps1` — entrypoint fino Windows

Ambos apenas garantem Python >= 3.10 no ambiente e delegam para
`scripts/bootstrap_repo/bootstrap.py`. Existem por causa do problema
ovo-e-galinha: o bootstrap é quem instala o Python.

**Conteúdo do `~/.bashrc`:** continua sendo bash, mas escrito pelo Python.
Com o fim do container crawl4ai sobra apenas `export` de variáveis.

**`tests/integration/docker/entrypoint.sh` → `entrypoint.py`:** a imagem é
`ubuntu:24.04`; basta acrescentar `python3` ao `apt-get install` do Dockerfile.

**Escopo da migração:**

| Categoria | Origem | Destino |
|---|---|---|
| Wrappers de skill | `opencode-doc-extract.sh`, `opencode-md-export.sh`, `opencode-svgtoimage.sh` | `.py` |
| Browser test | `browser-test/run`, `run.sh` (byte-idênticos — deduplicar), `install-playwright.sh` | `.py` |
| Bootstrap | `wsl-install-deps.sh` | `bootstrap.py` + módulos |
| Adapters | `copilot-cli-adapter.sh`, `copilot-cli-adapter.ps1`, `opencode-adapter.sh` | `.py` único |
| Sync upstream | `lib/sync-common.sh` + os 3 `*/sync.sh` | `.py` |
| Skills mgmt | `skills/list-updatable.sh`, `skills/update-upstream-skill.sh` | `.py` |
| Scaffold | `mapa-produto/scaffold.sh` | `.py` |
| Docker test | `container-test-opencode.sh`, `entrypoint.sh` | `.py` |
| Testes | 39 arquivos `.bats` (4.608 linhas) | pytest |
| **Removidos** | `crawl4ai/docker/*`, `crawl4ai/install-crawl4ai-mcp.sh`, `crawl4ai/start-crawl4ai.sh` | — |

**Ganho colateral:** os adapters `.sh` e `.ps1` do Copilot deixam de existir
como par, eliminando a regra de sincronização manual documentada no `AGENTS.md`.

### AD-5: OpenCode é exclusivo de WSL/Linux — REVISADO E APROVADO

**Decisão:** o OpenCode roda **apenas** em WSL/Linux. No Windows, o único
cliente configurado é o Copilot CLI.

**Consequências:**
- O adapter OpenCode permanece **Linux-only** e continua usando symlinks.
  Não precisa de junction, fallback de cópia nem suporte a Windows.
- O bootstrap Windows configura **somente** o Copilot CLI + as ferramentas CLI
  (`crwl`, `codebase-memory-mcp`, docling, pandoc etc.).
- O adapter Copilot continua **copiando** artefatos para `~/.copilot/` nos dois
  SOs (é conversão, não espelho) — comportamento já existente, mantido.
- A matriz de bootstrap fica:

| Ambiente | OpenCode adapter | Copilot adapter | Ferramentas CLI |
|---|---|---|---|
| WSL / Linux | sim (symlinks) | sim | sim |
| Windows | **não** | sim | sim |


### AD-6: Separação estrita de clientes por SO — APROVADO

**Decisão:** cada cliente roda em exatamente um ambiente.

| Ambiente | Cliente | Adapter | Ferramentas CLI |
|---|---|---|---|
| WSL / Linux | **OpenCode** | `opencode` (symlinks) | sim |
| Windows | **Copilot CLI** | `copilot-cli` (cópia) | sim |

**Consequências:**
- `configurar-repo` detecta o SO e executa **apenas** o adapter pertinente.
  Nunca os dois.
- O adapter Copilot deixa de precisar de versão bash; sob AD-4 vira um único
  script Python executado no Windows.
- O adapter OpenCode nunca roda no Windows.
- A reescrita `./scripts/X.sh` → `wsl bash <path>` no adapter Copilot é
  eliminada: sob AD-3 o Windows tem as ferramentas nativas.
- Testes ficam segmentados por ambiente: suíte OpenCode roda no WSL, suíte
  Copilot roda no Windows, e há um núcleo comum que roda nos dois.
- As variáveis `OPENCODE_SKIP_COPILOT_ADAPTER` / `OPENCODE_SKIP_OPENCODE_ADAPTER`
  perdem sentido como escolha manual — passam a ser consequência do SO
  detectado (podendo sobreviver como override de teste).

### AD-7: Websearch — preferência declarada com fallback — APROVADO

**Decisão:** a skill `web-research-exa-crawl4ai` passa a ser agnóstica de
cliente e declara a cadeia de preferência:

1. `web_search_exa` (Exa MCP remoto), se disponível
2. `websearch` nativa (OpenCode com `OPENCODE_ENABLE_EXA=1`), se disponível
3. busca padrão do ambiente (fallback)

**Consequências:**
- Remove-se a substituição hardcoded `websearch` → `web_search_exa` presente
  hoje em `copilot-cli-adapter.sh:208-212` e `copilot-cli-adapter.ps1:349-354`
  (funções `Adapt-SkillForCopilot` / equivalente bash).
- O Exa continua sendo MCP **remoto** — fora do escopo da eliminação de MCP
  local (AD-1) e sem chave de API nova para gerenciar.
- `OPENCODE_ENABLE_EXA=1` continua sendo garantido no `~/.bashrc` pelo
  bootstrap Linux.



### AD-8: pytest puro substitui o Makefile; deps de dev em `.venv` — APROVADO

**Decisão:** o `Makefile` é removido. Os targets viram marcadores pytest e a
orquestração vira fixtures.

| Target atual | Substituto |
|---|---|
| `make test-unit` | `pytest -m unit` |
| `make test-tools` | `pytest -m tools` |
| `make test-opencode` | `pytest -m "unit or tools or opencode"` |
| `make test-copilot` | `pytest -m "unit or tools or copilot"` |
| `make test-opencode-integration` | `pytest -m opencode` |
| `make test-copilot-integration` | `pytest -m copilot` |
| `trap ... --down` (cleanup Docker) | fixture session-scoped com teardown |
| guarda de `OPENCODE_TEST_MODEL` | `pytest.fail` na fixture |

**Motivação:** `make` não existe no Windows, onde a suíte Copilot roda (AD-6).
Fixtures dão cleanup garantido, hoje dependente de `trap`.

**Ambiente de dev:** `.venv` na raiz do repo, criada pelo bootstrap a partir de
`requirements-dev.txt`. Permite plugins de pytest (difícil via pipx) e funciona
igual nos dois SOs. `.venv/` entra no `.gitignore`.

**Marcadores registrados em `pyproject.toml`:**
`unit`, `tools`, `opencode`, `copilot`.



### AD-9: Estratégia zero-admin em todos os SOs — APROVADO

**Decisão:** nenhuma instalação exige privilégio elevado (`sudo` / admin). Tudo
em user-space ou binário portátil.

| Dependência | Método zero-admin |
|---|---|
| Python ≥ 3.10 | pré-requisito; Microsoft Store / python.org "just for me" / `winget --scope user` |
| Node.js | **fnm** (já usado no Linux); `fnm-windows.zip` é binário único |
| pipx | `pip install --user pipx` |
| `crwl` (crawl4ai) | `pipx install crawl4ai` + `crawl4ai-setup` |
| docling | `pipx install docling` |
| `codebase-memory-mcp` | `npm i -g` com prefix em user-space |
| pandoc | zip portátil oficial (alternativa ao MSI, documentada pelo próprio pandoc) |
| git | PortableGit (Windows) / já presente no Linux |
| Playwright + Chromium | `npx playwright install` → `%LOCALAPPDATA%\ms-playwright` |
| pytest + plugins | `.venv` do repo (AD-8) |
| AWS CLI v2 | script oficial em modo user-local (ver AD-13) |

**Duas simplificações descobertas na investigação:**

1. **Bloco `sudo` do Linux está inflado.** `tesseract-ocr`, `ocrmypdf`,
   `ghostscript` e `qpdf` **não são usados** por `opencode-doc-extract.sh` —
   ele invoca apenas `docling`, que embute o próprio motor de OCR. Devem sair
   do README e do bootstrap. Sobra `pandoc` (substituível por zip portátil) e
   `librsvg2-bin` (eliminado pelo item 2).

2. **`resvg` → Playwright.** Não existe binário Windows de `resvg` nos
   releases oficiais. Como o repo **já instala Playwright/Chromium** para a
   skill `browser-testing`, e o Chromium renderiza SVG e captura screenshot
   nativamente, `opencode-svgtoimage` passa a usar Playwright. Elimina
   `resvg`, `rsvg-convert` e `librsvg2-bin` de vez, nos dois SOs.

### AD-10: Bootstrap com detecção e seleção interativa — APROVADO

**Decisão:** o bootstrap faz uma passada de **detecção** antes de instalar
qualquer coisa, apresenta ao humano uma tabela do estado de cada dependência e
pergunta o que instalar.

**Fluxo:**
1. **Detectar** — para cada dependência: presente/ausente, versão encontrada,
   método de instalação previsto.
2. **Apresentar** — tabela com `nome | status | versão | método`.
3. **Perguntar** — humano escolhe o que o bootstrap instala e o que ele
   mesmo instalará por fora.
4. **Instalar** apenas o selecionado.
5. **Reportar** — para os não selecionados/não instaláveis, imprimir bloco
   único de comandos prontos para copiar e colar.

**Modos não interativos:**
- `--yes` — instala tudo que está ausente, sem perguntar.
- `--check-only` — só executa passos 1, 2 e 5; não instala nada.

**Motivação:** ferramentas podem já existir no ambiente (instaladas por fora,
versão corporativa, outra política de PATH). Sobrescrever cegamente é
destrutivo; o humano precisa poder optar por dependência.



### AD-11: Pacote Python instalável com `console_scripts` — APROVADO

**Decisão:** o repo vira um pacote Python (`pyproject.toml`) instalado com
`pipx install --editable .` pelo bootstrap. Os wrappers viram *entry points*.

**Por que:** os binários caem em `~/.local/bin` (Linux) e
`%LOCALAPPDATA%\pipx\bin` (Windows) — ambos já no PATH. O comando invocado pela
skill vira **a mesma string nos dois SOs**, o que elimina de vez a reescrita de
caminhos do adapter (`Rewrite-ScriptRefs` / `wsl bash`). `--editable` preserva a
propriedade "editar no repo reflete na hora", igual aos symlinks.

**Entry points:**

| Comando | Substitui |
|---|---|
| `opencode-doc-extract` | `scripts/opencode-doc-extract.sh` |
| `opencode-md-export` | `scripts/opencode-md-export.sh` |
| `opencode-svgtoimage` | `scripts/opencode-svgtoimage.sh` (agora via Playwright) |
| `opencode-browser-test` | `scripts/browser-test/run` + `run.sh` (deduplicados) |
| `opencode-bootstrap` | `scripts/bootstrap_repo/wsl-install-deps.sh` |
| `opencode-adapter` | `adapters/opencode/opencode-adapter.sh` |
| `copilot-adapter` | `copilot-cli-adapter.sh` + `.ps1` (unificados) |
| `opencode-skills` | `skills/list-updatable.sh` + `skills/update-upstream-skill.sh` + `*/sync.sh` |
| `opencode-scaffold-mapa` | `mapa-produto/scaffold.sh` |

**Estrutura proposta:**

```
pyproject.toml            # deps, entry points, config do pytest, marcadores
requirements-dev.txt      # pytest + plugins (.venv)
src/opencode_config/
  __init__.py
  cli/                    # um módulo por entry point
  lib/                    # código compartilhado (ex-sync-common.sh), detecção de SO,
                          # execução de processo, contrato JSON, PATH/user-space
  bootstrap/              # detecção de deps, instaladores zero-admin, seleção interativa
  adapters/               # opencode (symlink) e copilot (cópia/conversão)
tests/                    # pytest, espelhando src/
scripts/                  # apenas os 2 entrypoints shell (AD-4)
```

**Consequência para as skills:** todo SKILL.md passa a citar o comando direto
(`opencode-doc-extract`), sem caminho e sem `python`. O adapter Copilot copia o
SKILL.md **sem transformar** o comando.



### AD-12: Fatias verticais, fundação primeiro, remoção de MCP na sequência — APROVADO

**Decisão:** migração em fatias verticais. Cada fatia entrega script Python +
testes pytest + documentação + entry point, deixando o repo verde ao final.
BATS e pytest **coexistem** durante a transição; BATS só é aposentado na
fase 6.

**Motivação:** com 39 suítes de teste, uma migração por camada horizontal
criaria uma janela longa sem verificação possível — exatamente onde erros
silenciosos se acumulam. Em fatias verticais cada etapa é validável e o
trabalho pode ser interrompido/retomado sem deixar o repo inconsistente.

A remoção do MCP (fase 1) vem logo após a fundação por dois motivos: é o
pedido original (entrega valor cedo) e é a fatia de maior risco técnico
(falha rápido).

### AD-13: AWS CLI v2 como dependência obrigatória e gerenciada — APROVADO

**Decisão:** o AWS CLI v2 entra no registro de dependências do bootstrap como
**obrigatório nos dois SOs**, instalado pelo script oficial da AWS em modo
**user-local** (sem `sudo`, sem admin).

**Motivação:** o agente `aws-analista` opera inteiramente via `aws` CLI, e as
skills `aws-sso-login` e `aws-add-account-sso` têm como passo 1 do fluxo
"validar se o AWS CLI está disponível". O `opencode.json` concede permissão
dedicada `"aws-*": "allow"` ao agente. Apesar disso, a dependência **nunca
entrou no bootstrap** — figurava apenas como nota solta no `README.md:104`
("Dependência externa fora desse comando"). Nenhum script a detecta ou instala.

**Instaladores oficiais (ambos verificados nesta sessão):**

Invocação — Linux/WSL:

```bash
curl -fsSL https://awscli.amazonaws.com/v2/install.sh | bash
```

Invocação — Windows (PowerShell):

```powershell
irm https://awscli.amazonaws.com/v2/install.ps1 | iex
```

| | Linux/WSL | Windows |
|---|---|---|
| Script | `install.sh` (23.658 B) | `install.ps1` (15.594 B) |
| Default | user-local, **sem root** | user-local, **sem admin** |
| Destino | `$HOME/.local/share/aws-cli` + symlink em `$HOME/.local/bin` | `%LOCALAPPDATA%\Programs\Amazon\AWSCLIV2` |
| Escopo global | `--system` (exige root) | `-System` (exige admin) |
| Silencioso | `--quiet` | `-Quiet` |
| Pinar versão | `--version <X.Y.Z>` | `-Version <X.Y.Z>` |
| Ajuda | `--help` | `-Help` |

**Propriedades que sustentam a decisão:**

- Os dois scripts são **simétricos por design** — mesmos modos, mesma
  semântica, elevação sempre opt-in e nunca default.
- O Windows usa um MSI **dedicado por usuário** (`AWSCLIV2-User.msi`), publicado
  pela própria AWS — não é extração improvisada do MSI per-machine.
- O `install.ps1` verifica **assinatura Authenticode** do MSI antes de instalar.
- Ambos são **idempotentes**: detectam a versão instalada e saem com
  "nothing to do"; recusam downgrade com mensagem acionável.
- No Windows *"the MSI manages PATH"* — o bootstrap não precisa mexer no PATH.
- No Linux respeitam `XDG_DATA_HOME`/`XDG_BIN_HOME`, e o default
  `$HOME/.local/bin` é exatamente a convenção que AD-9 já adota.
- Ambos falham cedo e com mensagem explícita se `--system`/`-System` for pedido
  sem privilégio — nunca degradam silenciosamente.

**Nota de pesquisa:** a documentação espelhada em
`awsdocs/aws-cli-user-guide` (GitHub) está **desatualizada** na seção Windows —
afirma "Admin rights to install software" sem qualificador e não menciona o
script. A página viva em `docs.aws.amazon.com` traz "(if installing for all
users)" e as três abas *Install script (recommended)*, *MSI installer - All
users*, *MSI installer - Current user*. Consultar sempre a página viva.

**Sem risco novo:** não há workaround envolvido, então nenhum risco específico
é criado. Falha de download por proxy corporativo já está coberta por R5.

## Skills de Referência (obrigatórias para o executor)

O executor deve carregar e aplicar estas skills ao longo de todo o plano:

| Skill | Onde se aplica |
|---|---|
| `planning-and-task-breakdown` | Estrutura deste plano; quebrar task que crescer |
| `test-driven-development` | Toda fase: teste pytest antes da implementação Python |
| `tests-as-spec` | Traduzir cada `.bats` em spec antes de reescrever em pytest |
| `code-explorer-priority` | Descoberta de código antes de qualquer grep/glob |
| `api-and-interface-design` | Contrato JSON dos wrappers e assinatura dos entry points |
| `code-simplification` | Fases 2–5: os wrappers bash têm complexidade acidental a eliminar |
| `code-review-and-quality` | Checkpoint de cada fase, antes de seguir |
| `debugging-and-error-recovery` | Qualquer falha de teste ou desvio de comportamento |
| `security-and-hardening` | Fase 4: download de binários portáteis, verificação de SHA, escrita em PATH |
| `documentation-and-adrs` | Fase 1 e 6: registrar as decisões AD-1..AD-13 como ADRs |
| `git-workflow-and-versioning` | Commits por fatia, Conventional Commits |
| `caveman` | Formato das mensagens de commit |
| `spec-driven-development` | Fase 4: comportamento do bootstrap interativo precisa de spec antes do código |

## Task List

### Fase 0: Fundação

#### Task 0.1: Criar pacote Python e ambiente de desenvolvimento

**Description:** Criar `pyproject.toml` declarando o pacote
`opencode_config` em `src/`, as dependências de runtime, os entry points
(inicialmente vazios, preenchidos por fase) e a configuração do pytest com os
marcadores `unit`, `tools`, `opencode`, `copilot`. Criar
`requirements-dev.txt` e documentar a criação da `.venv`.

**Acceptance criteria:**
- [x] `pip install -e .` funciona a partir da raiz do repo
- [x] `pipx install --editable .` funciona
- [x] `pytest --markers` lista os 4 marcadores registrados
- [x] `.venv/`, `*.egg-info/`, `__pycache__/` no `.gitignore`

**Verification:**
- [x] `python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/pip install -e .`
- [x] `.venv/bin/pytest --collect-only` retorna 0 testes sem erro

**Dependencies:** None

**Files likely touched:** `pyproject.toml`, `requirements-dev.txt`,
`.gitignore`, `src/opencode_config/__init__.py`

**Estimated scope:** S

---

#### Task 0.2: Biblioteca compartilhada (`lib/`)

**Description:** Implementar os módulos base que todas as fases seguintes
consomem: detecção de ambiente (`linux` / `wsl` / `windows`), execução de
subprocesso com captura e timeout, contrato de saída JSON usado pelos wrappers
de skill (`{ok, engine, artifacts, stdout, stderr, hint}`), resolução de
diretórios user-space por SO, e manipulação idempotente de blocos marcados em
arquivos de config (`~/.bashrc`).

**Acceptance criteria:**
- [x] Detecção distingue corretamente Linux nativo, WSL e Windows
- [x] Contrato JSON tem uma única implementação, reutilizada por todos os wrappers
- [x] Escrita de bloco marcado é idempotente (aplicar 2x = mesmo resultado)
- [x] Nenhum módulo de `lib/` importa código específico de SO no import time

**Verification:**
- [x] `pytest -m unit tests/lib/` passa
- [x] Testes de detecção de SO cobrem os 3 ambientes via monkeypatch

**Dependencies:** 0.1

**Files likely touched:** `src/opencode_config/lib/*.py`, `tests/lib/*.py`

**Estimated scope:** M

**Skills:** `test-driven-development`, `api-and-interface-design`

---

#### Task 0.3: Infraestrutura pytest coexistindo com BATS

**Description:** Criar `tests/conftest.py` com fixtures base (repo root,
`HOME` temporário isolado, factory de repo fake) e garantir que o Makefile
atual continue funcionando enquanto o pytest é introduzido. Nenhuma suíte BATS
é removida nesta fase.

**Acceptance criteria:**
- [x] `pytest -m unit` roda e passa (mesmo que com poucos testes)
- [x] `make test-unit` continua passando sem alteração de comportamento
- [x] Fixture de `HOME` temporário impede que testes escrevam no `HOME` real

**Verification:**
- [x] `pytest -m unit` e `make test-unit` ambos verdes na mesma árvore

**Dependencies:** 0.1

**Files likely touched:** `tests/conftest.py`, `pyproject.toml`

**Estimated scope:** S

---

### Checkpoint: Fundação
- [x] `pipx install --editable .` instala o pacote
- [x] `pytest -m unit` verde
- [x] `make test-unit` (BATS) ainda verde — nenhuma regressão introduzida
- [x] Revisão com o humano antes de prosseguir

---

### Fase 1: Remoção do MCP (pedido original)

#### Task 1.1: Remover o container e os artefatos Docker do crawl4ai

**Description:** Deletar `scripts/crawl4ai/docker/` (Dockerfile,
`build.sh`, `sanitize_mcp.py`, `sitecustomize.py`),
`scripts/crawl4ai/install-crawl4ai-mcp.sh` e
`scripts/crawl4ai/start-crawl4ai.sh`. Remover o bloco marcado
`# Crawl4AI MCP - INICIO/FIM` do `~/.bashrc` de forma idempotente (o bootstrap
passa a limpar o bloco legado). Remover as suítes BATS correspondentes.

**Acceptance criteria:**
- [x] Nenhum arquivo sob `scripts/crawl4ai/` referencia Docker ou MCP
- [x] Bootstrap remove o bloco legado do `~/.bashrc` se presente
- [x] `tests/scripts/crawl4ai/install-crawl4ai-mcp-test.bats` e
      `start-crawl4ai-test.bats` removidos
- [x] `tests/scripts/doctree/` removido — suíte órfã, testa
      `scripts/doctree/install.sh` que não existe (ver Q3)
- [x] `grep -ri "crawl4ai-sanitized\|11235" ` não retorna nada no repo

**Verification:**
- [x] `make test-tools` verde após a remoção
- [x] `docker images | grep crawl4ai-sanitized` pode ser limpo manualmente

**Dependencies:** 0.1

**Files likely touched:** `scripts/crawl4ai/**` (removido),
`tests/scripts/crawl4ai/**`, `README.md`

**Estimated scope:** M

**Skills:** `git-workflow-and-versioning` (usar `git rm`, não recriar)

---

#### Task 1.2: Remover o wrapper `avelino/mcp`

**Description:** Remover a instalação do binário `mcp` de
`wsl-install-deps.sh` (bloco `# --- mcp (avelino) ---`, l.573+), a geração de
`~/.config/mcp/servers.json` dos dois adapters (`sync_mcp_cli` no `.sh`,
`Sync-McpCli` no `.ps1`), a guarda `command -v mcp` do target
`test-copilot-integration` no Makefile, e as 7 suítes BATS `mcp-avelino:*`.

**Acceptance criteria:**
- [x] `grep -ri "avelino"` não retorna nada fora de `plan/`
- [x] Adapters não escrevem mais `~/.config/mcp/servers.json`
- [x] `tests/integration/copilot-mcp-test.bats` removido
- [x] Testes de adapter que asseguravam `servers.json` removidos ou reescritos

**Verification:**
- [x] `make test-unit` verde
- [x] Rodar ambos os adapters num `HOME` temporário não cria `.config/mcp/`

**Dependencies:** 1.1

**Files likely touched:** `scripts/bootstrap_repo/wsl-install-deps.sh`,
`adapters/copilot-cli/copilot-cli-adapter.sh`, `.ps1`, `Makefile`,
`tests/scripts/bootstrap_repo/wsl-install-deps-test.bats`,
`tests/adapters/copilot-cli/*`, `tests/integration/copilot-mcp-test.bats`

**Estimated scope:** L — **candidata a quebrar em 1.2a (bootstrap) e
1.2b (adapters + testes)** se passar de 5 arquivos por commit

---

#### Task 1.3: Zerar o bloco `mcp` do `opencode.json`

**Description:** Remover as entradas `crawl4ai` e `codebase-memory` do
`opencode.json` e da config de teste `tests/integration/config/opencode.test.json`.
Remover o pós-processamento de `opencode.json` feito por
`scripts/codebase-memory/install.sh` (correção de path e deduplicação via `jq`),
que existia só para consertar a entrada MCP.

**Acceptance criteria:**
- [x] `opencode.json` não contém a chave `mcp` (ou contém `{}`)
- [x] `codebase-memory/install.sh` não edita mais `opencode.json`
- [x] `codebase-memory-mcp install -y` deixa de ser invocado (instalava skills MCP)
- [x] `auto_index=true` continua sendo configurado — é config do binário, não
      do transporte MCP (ver Q2)
- [x] O binário `codebase-memory-mcp` continua sendo instalado (é o CLI)

**Verification:**
- [x] `pytest`/BATS de integração MCP removidos e suíte verde
- [x] `codebase-memory-mcp cli list_projects '{}'` responde JSON válido

**Dependencies:** 1.2

**Files likely touched:** `opencode.json`,
`tests/integration/config/opencode.test.json`,
`scripts/codebase-memory/install.sh`, `tests/integration/mcp-test.bats`,
`tests/integration/mcp-mock/**`

**Estimated scope:** M

---

#### Task 1.4: Reescrever a skill `web-research-exa-crawl4ai`

**Description:** Substituir as tools MCP pelo CLI `crwl` conforme o mapeamento
de AD-2, e implementar a cadeia de preferência de websearch de AD-7
(`web_search_exa` → `websearch` → padrão do ambiente). Incluir exemplos
prontos de cada operação, já que screenshot/pdf têm sintaxe menos óbvia.
Substituir a seção "Resiliencia a rate limits (429)" — que descrevia erro do
MCP HTTP — pelo tratamento de falha equivalente do CLI (exit code, timeout,
bloqueio do site).

**Acceptance criteria:**
- [x] Nenhuma menção a `crawl4ai_md`, `crawl4ai_html`, `crawl4ai_execute_js`,
      `crawl4ai_screenshot`, `crawl4ai_pdf`
- [x] Cadeia de fallback de websearch declarada explicitamente
- [x] Um exemplo executável por operação (md, html, js, screenshot, pdf, deep)
- [x] Fallback para `doc-extract` em URLs binárias preservado
- [x] `description` do frontmatter continua carregando os triggers de ativação

**Verification:**
- [x] `pytest -m unit tests/skills/test_web_research.py` (porte do `.bats`)
- [x] Execução manual: `crwl https://example.com -o md-fit` retorna markdown

**Dependencies:** 1.1

**Files likely touched:** `skills/web-research-exa-crawl4ai/SKILL.md`,
`tests/skills/web-research-exa-crawl4ai-test.bats` → `tests/skills/test_web_research.py`

**Estimated scope:** M

**Skills:** `tests-as-spec` (o `.bats` atual é a spec do comportamento)

---

#### Task 1.5: Reescrever as instruções de descoberta de código

**Description:** Trocar o wrapper `mcp codebase-memory <tool>` por
`codebase-memory-mcp cli <tool> '<json>'` em: `AGENTS.md` (seções
"Descoberta de Codigo", "Acesso MCP por Cliente"),
`.github/copilot-specific.instructions.md` (o arquivo inteiro gira em torno do
wrapper), `skills/code-explorer-priority/SKILL.md`,
`commands/index-codebase.md` e `commands/bench-indexing.md`. Ajustar a tabela
"Acesso MCP por Cliente" para refletir AD-6 (OpenCode = WSL, Copilot = Windows)
e o fato de que **ambos** agora usam o mesmo CLI.

**Acceptance criteria:**
- [x] Nenhum documento instrui `mcp <servidor> <tool>`
- [x] Sintaxe documentada validada: `codebase-memory-mcp cli list_projects '{}'`
- [x] A regra "MCP antes de grep/glob" vira "CLI antes de grep/glob", sem
      perder força imperativa
- [x] Instruções de recovery ("project not found" → `list_projects` → re-tentar)
      preservadas

**Verification:**
- [x] `pytest -m unit tests/skills/test_code_explorer.py` (porte do `.bats`)
- [x] `grep -rn "mcp --list\|mcp codebase-memory\|mcp crawl4ai"` retorna vazio

**Dependencies:** 1.2

**Files likely touched:** `AGENTS.md`,
`.github/copilot-specific.instructions.md`,
`skills/code-explorer-priority/SKILL.md`, `commands/index-codebase.md`,
`commands/bench-indexing.md`, `agents/curador-produto-editor.md`,
`docs/workflow-curadoria.md`, `tests/skills/code-explorer-priority-test.bats`

**Estimated scope:** M

---

#### Task 1.6: Remover a substituição `websearch` → `web_search_exa`

**Description:** Eliminar a reescrita hardcoded dos dois adapters
(`copilot-cli-adapter.sh:208-212` e `copilot-cli-adapter.ps1:349-354`), já que
AD-7 move a lógica de preferência para dentro da própria skill.

**Acceptance criteria:**
- [x] Nenhum adapter transforma o texto da skill `web-research-exa-crawl4ai`
- [x] SKILL.md copiado para `~/.copilot/skills/` é byte-idêntico ao do repo
      (exceto normalização de frontmatter)

**Verification:**
- [x] `pytest`/BATS de adapter verde
- [x] `diff` entre `skills/web-research-exa-crawl4ai/SKILL.md` e a cópia gerada

**Dependencies:** 1.4

**Files likely touched:** `adapters/copilot-cli/copilot-cli-adapter.sh`,
`.ps1`, `tests/adapters/copilot-cli/*`

**Estimated scope:** S

---

#### Task 1.7: Instalar `crwl` no bootstrap

**Description:** Acrescentar `crawl4ai` via pipx + `crawl4ai-setup` ao
`wsl-install-deps.sh` (ainda em bash — a migração para Python é a fase 4),
substituindo o bloco que instalava o `mcp`. Verificação de presença via
`command -v crwl`.

**Acceptance criteria:**
- [x] Bootstrap detecta `crwl` já instalado e não reinstala
- [x] `crawl4ai-setup` é executado após a instalação (baixa o browser)
- [x] Falha de instalação reporta hint acionável, não aborta o bootstrap inteiro

**Verification:**
- [x] Testes BATS de `wsl-install-deps` cobrindo presente/ausente
- [x] `crwl --help` responde após bootstrap num ambiente limpo

**Dependencies:** 1.2

**Files likely touched:** `scripts/bootstrap_repo/wsl-install-deps.sh`,
`tests/scripts/bootstrap_repo/wsl-install-deps-test.bats`, `README.md`

**Estimated scope:** S

---

#### Task 1.8: Atualizar documentação da fase 1

**Description:** Atualizar `README.md` (seções Bootstrap e Dependências —
remover `mcp (avelino)` e o container crawl4ai, adicionar `crwl`, e promover o
AWS CLI de "dependência externa fora desse comando" (`README.md:104`) a
dependência obrigatória gerenciada pelo bootstrap, conforme AD-13),
`AGENTS.md` (seção Bootstrap, variáveis `OPENCODE_SKIP_*`) e
`agents/default-artifacts/doc-readme.md:127` (linha do codebase-memory que
descreve acesso "via MCP"). Registrar as decisões AD-1..AD-13 como ADR.

**Acceptance criteria:**
- [x] README não menciona MCP local, Docker ou `mcp (avelino)`
- [x] Variáveis de skip documentadas refletem a realidade pós-mudança
- [x] ADR criado em `docs/adr/` cobrindo a eliminação de MCP
- [x] AWS CLI aparece na tabela de dependências do README, não como nota solta
- [x] Nenhuma linha de MD passa de 120 colunas

**Verification:**
- [x] `grep -rn "avelino\|11235\|mcp/sse"` retorna apenas `plan/` e `docs/adr/`

**Dependencies:** 1.1, 1.2, 1.3, 1.4, 1.5, 1.7

**Files likely touched:** `README.md`, `AGENTS.md`,
`agents/default-artifacts/doc-readme.md`, `docs/adr/*.md`

**Estimated scope:** M

**Skills:** `documentation-and-adrs`

---

### Checkpoint: MCP eliminado
- [x] `grep -ri "avelino\|crawl4ai-sanitized\|mcp/sse\|11235"` limpo
- [x] `opencode.json` sem bloco `mcp`
- [x] `crwl` e `codebase-memory-mcp cli` funcionam no WSL
- [ ] `pytest -m opencode` verde — bloqueado por Docker/`OPENCODE_TEST_MODEL`
- [x] Skills `web-research-exa-crawl4ai` e `code-explorer-priority` validadas
      em execução real (não só por grep)
- [x] Revisão com o humano antes de prosseguir

> `pytest -m opencode` permanece pendente porque requer
> `OPENCODE_TEST_MODEL`; o bloqueio foi aceito explicitamente para seguir.

---

### Fase 2: Wrappers de skill → Python

> As tasks 2.1–2.4 são **independentes entre si** e podem ser paralelizadas.
> Todas seguem o mesmo padrão: porte do `.bats` para spec (`tests-as-spec`),
> teste pytest antes do código (`test-driven-development`), entry point no
> `pyproject.toml`, atualização do SKILL.md para chamar o comando sem caminho.

#### Task 2.1: `opencode-doc-extract`

**Description:** Portar `scripts/opencode-doc-extract.sh` (198 linhas) para
`src/opencode_config/cli/doc_extract.py`, mantendo o contrato JSON stdin→stdout.
Usar o módulo de contrato JSON de `lib/` (Task 0.2). Confirmar e documentar que
o OCR é feito pelo próprio docling — sem `tesseract`/`ocrmypdf`.

**Acceptance criteria:**
- [x] Contrato JSON de entrada e saída idêntico ao do script bash
- [x] Mensagens de erro e `hint` de instalação preservadas e adaptadas por SO
- [x] `opencode-doc-extract` disponível no PATH após `pipx install --editable .`
- [x] `skills/doc-extract/SKILL.md` chama `opencode-doc-extract` sem caminho

**Verification:**
- [x] `pytest -m tools tests/cli/test_doc_extract.py` (porte de
      `opencode-doc-extract-test.bats`, 136 linhas)
- [x] Extração real de um PDF de `tests/test-resources/`

**Dependencies:** 0.2

**Files likely touched:** `src/opencode_config/cli/doc_extract.py`,
`tests/cli/test_doc_extract.py`, `skills/doc-extract/SKILL.md`,
`pyproject.toml`, `scripts/opencode-doc-extract.sh` (removido)

**Estimated scope:** M

---

#### Task 2.2: `opencode-md-export`

**Description:** Portar `scripts/opencode-md-export.sh` (191 linhas) para
`src/opencode_config/cli/md_export.py`. Adaptar o `PANDOC_INSTALL_HINT` para a
estratégia zero-admin de AD-9 (zip portátil no Windows).

**Acceptance criteria:**
- [x] Conversões docx/pptx/xlsx produzem os mesmos artefatos do script bash
- [x] Localiza o `pandoc` tanto no PATH quanto no diretório portátil do repo
- [x] `skills/md-export/SKILL.md` chama `opencode-md-export`

**Verification:**
- [x] `pytest -m tools tests/cli/test_md_export.py` (porte de
      `opencode-md-export-test.bats`, 179 linhas)

**Dependencies:** 0.2

**Files likely touched:** `src/opencode_config/cli/md_export.py`,
`tests/cli/test_md_export.py`, `skills/md-export/SKILL.md`, `pyproject.toml`

**Estimated scope:** M

---

#### Task 2.3: `opencode-svgtoimage` via Playwright

**Description:** Reimplementar SVG→PNG usando Playwright/Chromium em vez de
`resvg`/`rsvg-convert` (AD-9, item 2). Remover `librsvg2-bin` do bootstrap e do
README. Manter o contrato de entrada (SVG via stdin) e a variável de override
se ainda fizer sentido.

**Acceptance criteria:**
- [x] PNG gerado a partir de SVG via stdin, com dimensões corretas
- [x] Funciona sem `resvg` e sem `rsvg-convert` instalados
- [x] Reaproveita a instalação de Playwright da skill `browser-testing` — não
      instala um segundo browser
- [x] `skills/svg-to-image/SKILL.md` atualizado

**Verification:**
- [x] `pytest -m tools tests/cli/test_svgtoimage.py` (porte de
      `opencode-svgtoimage-test.bats`, 83 linhas)
- [x] Comparação visual/dimensional com a saída do `resvg` atual

**Dependencies:** 0.2

**Files likely touched:** `src/opencode_config/cli/svgtoimage.py`,
`tests/cli/test_svgtoimage.py`, `skills/svg-to-image/SKILL.md`,
`scripts/bootstrap_repo/wsl-install-deps.sh`, `README.md`

**Estimated scope:** M

**Risco:** mudança de engine de renderização pode alterar o resultado
visual — validar antes de descartar o `resvg`.

---

#### Task 2.4: `opencode-browser-test`

**Description:** Portar `scripts/browser-test/run` para
`src/opencode_config/cli/browser_test.py`, **eliminando a duplicação** com
`run.sh` (são byte-idênticos). A instalação do Playwright
(`install-playwright.sh`, 190 linhas) migra para o motor de bootstrap da
fase 4 — aqui apenas a execução.

**Acceptance criteria:**
- [x] `run` e `run.sh` removidos; um único entry point
- [x] Cleanup do script temporário garantido mesmo em falha (equivalente ao `trap`)
- [x] Contrato JSON de saída preservado
- [x] `skills/browser-testing/SKILL.md` atualizado

**Verification:**
- [x] `pytest -m tools tests/cli/test_browser_test.py` (porte de
      `run-test.bats`, 132 linhas)
- [x] Execução real de um teste Playwright trivial

**Dependencies:** 0.2

**Files likely touched:** `src/opencode_config/cli/browser_test.py`,
`tests/cli/test_browser_test.py`, `skills/browser-testing/SKILL.md`,
`scripts/browser-test/**` (removido)

**Estimated scope:** M

---

### Checkpoint: Wrappers migrados
- [x] Os 4 entry points respondem no PATH após `pipx install --editable .`
- [x] `pytest -m "unit or tools"` verde
- [x] Nenhum SKILL.md referencia caminho de script
- [x] Suítes legadas equivalentes passaram antes da remoção final do BATS
- [x] Revisão com o humano

> A verificação de integração permaneceu condicionada ao servidor OpenCode em
> `127.0.0.1:4196`; os testes direcionados da área modificada ficaram verdes.

---

### Fase 3: Adapters → Python unificado

#### Task 3.1: `opencode-adapter`

**Description:** Portar `adapters/opencode/opencode-adapter.sh` (338 linhas)
para Python. Permanece **Linux-only** (AD-5): symlinks, backup com timestamp e
gestão de blocos no `~/.bashrc`. Deve **falhar com mensagem clara** se invocado
no Windows.

**Acceptance criteria:**
- [x] Symlinks criados em `~/.config/opencode` para agents, commands, skills,
      scripts e `opencode.json`
- [x] Backup em `~/.config/opencode-backup/<timestamp>` quando o destino existe
- [x] Idempotente: rodar 2x não gera backup espúrio
- [x] Blocos do `~/.bashrc` (PATH, `OPENCODE_ENABLE_EXA`) idempotentes
- [x] Recusa executar no Windows com mensagem explicativa

**Verification:**
- [x] `pytest -m unit tests/adapters/test_opencode_adapter.py` (porte de
      `opencode-adapter-test.bats`) usando `HOME` temporário
- [x] Bootstrap executa o módulo Python e `opencode-adapter --help` responde

**Dependencies:** 0.2, fase 2 completa

**Files touched:** `src/opencode_config/adapters/opencode.py`,
`tests/adapters/test_opencode_adapter.py`, `pyproject.toml`,
`scripts/bootstrap_repo/configurar-repo.sh`,
`adapters/opencode/opencode-adapter.sh` (removido), documentação e BATS
dependentes atualizados

**Estimated scope:** M

---

#### Task 3.2: `copilot-adapter` unificado

**Description:** Fundir `copilot-cli-adapter.sh` (491) e
`copilot-cli-adapter.ps1` (583) num único módulo Python. Elimina: geração de
`servers.json` (feito na 1.2), substituição de websearch (1.6) e **toda a
`Rewrite-ScriptRefs`/`wsl bash`** — desnecessária sob AD-3/AD-11, pois os
comandos são os mesmos nos dois SOs. Passa a ser **Windows-first** (AD-6),
ainda executável no Linux para testes.

**Acceptance criteria:**
- [x] Um único código-fonte; `.sh` e `.ps1` removidos
- [x] Conversão de frontmatter de agentes e de commands→skills preservada
- [x] Validação de nome de skill e frontmatter preservada
- [x] Nenhuma reescrita de caminho de script no SKILL.md copiado
- [x] A regra de sincronização `.sh`/`.ps1` sai do `AGENTS.md` (não há mais par)

**Verification:**
- [x] `pytest -m unit tests/adapters/test_copilot_adapter.py` (porte de
      `copilot-cli-adapter-test.bats` + `-ps1-test.bats`)
- [x] Execução com `--dest-root` temporário produz a árvore esperada
- [ ] Execução real no Windows produz `%USERPROFILE%\.copilot\` funcional
      (adiada para a validação multiplataforma final pelo humano)

**Dependencies:** 3.1

**Files likely touched:** `src/opencode_config/adapters/copilot.py`,
`tests/adapters/test_copilot_adapter.py`, `adapters/copilot-cli/**` (removido),
`AGENTS.md`

**Estimated scope:** L — **quebrar em 3.2a (conversão de artefatos) e
3.2b (validação + frontmatter)** se necessário

---

### Checkpoint: Adapters migrados
- [x] Um único adapter por cliente, em Python
- [x] `pytest -m unit` verde
- [ ] Adapter Copilot validado **no Windows real**, não só em mock
- [x] `AGENTS.md` sem a regra de sincronização `.sh`/`.ps1`
- [ ] Revisão com o humano

---

### Fase 4: Bootstrap Python multiplataforma

#### Task 4.1: Motor de detecção de dependências

**Description:** Implementar o passo 1 de AD-10: um registro declarativo de
dependências (nome, comando de verificação, extrator de versão, método de
instalação por SO, obrigatória/opcional) e o motor que o percorre produzindo o
estado de cada uma.

**Acceptance criteria:**
- [x] Registro é declarativo — acrescentar dependência não exige código novo
- [x] Detecção reporta: presente/ausente, versão, caminho, método previsto
- [x] Nenhuma instalação ocorre na fase de detecção
- [x] Cobre as dependências da tabela de AD-9, incluindo o AWS CLI (AD-13)

**Verification:**
- [x] `pytest -m unit tests/bootstrap/test_detect.py` com PATH mockado

**Dependencies:** 0.2

**Files likely touched:** `src/opencode_config/bootstrap/registry.py`,
`detect.py`, `tests/bootstrap/test_detect.py`

**Estimated scope:** M

**Skills:** `spec-driven-development` (especificar o comportamento antes)

---

#### Task 4.2: Instaladores zero-admin

**Description:** Implementar os instaladores de AD-9: pipx, `npm -g` com prefix
user-space, fnm (binário portátil, incl. `fnm-windows.zip`), pandoc portátil,
PortableGit, `crawl4ai-setup`, `npx playwright install`, AWS CLI v2 (AD-13) e a
criação da `.venv`. Downloads devem verificar SHA quando o upstream publicar.

**Acceptance criteria:**
- [x] Nenhum instalador requer `sudo` ou elevação
- [x] Binários portáteis vão para um diretório user-space único e o PATH é
      atualizado de forma idempotente
- [x] Download verifica integridade quando houver SHA publicado; aborta se
      divergir, exibindo ambos os hashes
- [x] Falha de uma dependência não aborta as demais
- [x] AWS CLI instalado pelo script oficial em modo user-local, com `--quiet` /
      `-Quiet`, e **nunca** com `--system` / `-System`
- [x] Reexecutar o instalador do AWS CLI é no-op quando já está na versão alvo

**Verification:**
- [x] `pytest -m unit tests/bootstrap/test_installers.py` com rede mockada
- [ ] Instalação real ponta-a-ponta num Windows sem admin
      (adiada para a validação multiplataforma final pelo humano)

**Dependencies:** 4.1

**Files likely touched:** `src/opencode_config/bootstrap/installers/*.py`,
`tests/bootstrap/test_installers.py`

**Estimated scope:** L — **quebrar por família de instalador**
(python/pipx, node/fnm/npm, binários portáteis)

**Skills:** `security-and-hardening` (download de binário, verificação de
integridade, escrita em PATH)

---

#### Task 4.3: Seleção interativa

**Description:** Implementar os passos 2–5 de AD-10: apresentar a tabela de
estado, perguntar ao humano o que instalar, instalar apenas o selecionado e
imprimir bloco único copiável para o restante. Suportar `--yes` (instala tudo
que falta) e `--check-only` (não instala nada).

**Acceptance criteria:**
- [x] Tabela mostra nome, status, versão e método por dependência
- [x] Seleção por item, com default sensato
- [x] Sem TTY, `--yes` é obrigatório — erro claro caso contrário
- [x] `--check-only` não altera nada no sistema
- [x] Bloco de comandos manuais sai em **um único bloco** copiável

**Verification:**
- [x] `pytest -m unit tests/bootstrap/test_interactive.py` com stdin simulado
- [x] `--check-only` num ambiente sujo não modifica nada (verificado por hash
      do `HOME` temporário antes/depois)

**Dependencies:** 4.2

**Files likely touched:** `src/opencode_config/bootstrap/interactive.py`,
`tests/bootstrap/test_interactive.py`

**Estimated scope:** M

---

#### Task 4.4: Entrypoints `configurar-repo.sh` e `configurar-repo.ps1`

**Description:** Reduzir `configurar-repo.sh` (197 linhas) a um entrypoint
fino e criar o par `.ps1`. Ambos: verificam Python ≥ 3.10, orientam a
instalação zero-admin se ausente, e delegam para `opencode-bootstrap`. A
seleção de adapter passa a ser **derivada do SO** (AD-6), não de flag.

**Acceptance criteria:**
- [x] Cada entrypoint tem ≤ ~40 linhas e nenhuma lógica de negócio
- [x] Python ausente → mensagem acionável específica do SO, sem stack trace
- [x] No Linux roda o adapter OpenCode; no Windows, o Copilot; nunca ambos
- [x] `--yes`, `--quiet`, `--check-only` repassados corretamente

**Verification:**
- [x] `pytest -m unit tests/bootstrap/test_entrypoints.py` (porte de
      `configurar-repo-test.bats`, 132 linhas)
- [x] `bash scripts/bootstrap_repo/configurar-repo.sh --check-only` no WSL
- [ ] `.\scripts\bootstrap_repo\configurar-repo.ps1 -CheckOnly` no Windows
      (adiado para a validação multiplataforma final pelo humano)

**Dependencies:** 4.3, 3.2

**Files likely touched:** `scripts/bootstrap_repo/configurar-repo.sh`,
`configurar-repo.ps1`, `wsl-install-deps.sh` (removido),
`tests/bootstrap/test_entrypoints.py`

**Estimated scope:** M

---

#### Task 4.5: Validação ponta-a-ponta no Windows

**Description:** Executar o bootstrap completo numa máquina Windows **sem
privilégio de administrador** e validar que todas as skills do Copilot
funcionam: web-research (`crwl`), code discovery (`codebase-memory-mcp cli`),
doc-extract, md-export, svg-to-image, browser-testing.

**Acceptance criteria:**
- [x] Bootstrap completa sem pedir elevação
- [x] Os 6 fluxos de skill executam com sucesso no Windows
- [x] `%USERPROFILE%\.copilot\` populado corretamente
- [x] Nenhum comando de skill contém `wsl` ou caminho `/mnt/c`

**Verification:**
- [x] `pytest -m copilot` verde executado **no Windows**
- [x] Checklist manual das 6 skills

**Resultado da validação Windows (2026-08-10):**
- **FAIL / bloqueada (R1):** execução nativa em PowerShell, sem WSL e sem
  elevação, a partir de `C:\Users\ur5y\Projetos\opencode-config`.
- `--check-only` terminou com exit `0`, mas reportou Python incompatível e
  dependências pendentes.
- `--yes` terminou com exit `1`; o adapter Copilot sincronizou os artefatos,
  mas `pipx`, `crwl`, Docling, codebase-memory, Pandoc, Playwright, AWS CLI e
  Copilot permaneceram ausentes.
- Nenhum prompt UAC, bloqueio de `.ps1` ou bloqueio de download portátil foi
  observado.
- `%USERPROFILE%\.copilot\` foi populado com `skills`, `agents`,
  `default-artifacts` e `instructions`.
- `crwl` não estava no PATH; a execução de `https://example.com` e os demais
  cinco fluxos foram interrompidos conforme o gatilho R1. O comportamento do
  `crwl` no Windows permanece não validado.
- `pytest -m copilot`, o conjunto Windows e a inspeção de comandos proibidos
  não foram executados.
- Evidências: `C:\Users\ur5y\AppData\Local\Temp\opencode-config-windows-validation`.

**Correção autorizada após a falha (2026-08-10):**
- A detecção Windows prioriza `python` antes do alias `python3`.
- O bootstrap persiste diretórios user-space no PATH do usuário, inclui o
  diretório real de scripts do `pipx` e usa o prefixo npm correto no Windows.
- O pacote `opencode-config` passa a ser instalado via
  `pipx install --editable .`, disponibilizando os entry points das skills.
- Falhas de instalação passam a aparecer no bloco de comandos manuais.
- Testes WSL: `359 passed, 26 deselected`.
- A nova execução Windows permanece pendente; os seis fluxos ainda não foram
  validados após a correção.

**Resultado da segunda validação Windows (2026-08-10):**
- A detecção do Python passou a funcionar (`3.14.0`).
- `--check-only` terminou com exit `0`; `--yes` terminou com exit `1`.
- `pipx` e `npm` continuaram indisponíveis dentro do processo do bootstrap.
- `pytest -m copilot` falhou na coleta com 8 erros `ModuleNotFoundError:
  opencode_config`.
- Os seis fluxos de skill continuaram sem execução; o bloqueio R1 permanece
  sem avaliação porque `crwl` não chegou a ser instalado.
- Nenhum UAC, bloqueio de `.ps1` ou alteração inesperada no Git foi observado.
- Evidências: `C:\Users\ur5y\AppData\Local\Temp\opencode-config-windows-validation-20260810-1106`.

**Correção adicional após a segunda validação (2026-08-10):**
- PATH agora é atualizado de forma case-insensitive, preservando a chave
  Windows `Path` e evitando uma segunda chave `PATH`.
- Detecção e instaladores usam o PATH real do ambiente, independentemente da
  capitalização.
- `install_pytest` instala o pacote do repositório em modo editável no `.venv`.
- Em Linux, a comparação de entradas do PATH continua case-sensitive.
- A detecção valida que o `.venv` importa `opencode_config`, mesmo quando há
  `pytest` global; `PYTHONPATH` do bootstrap não mascara essa verificação.
- Regressões direcionadas: `37 passed`; suíte WSL: `364 passed, 26 deselected`.
- No Windows, uma nova sessão PowerShell deve ser aberta após o bootstrap para
  carregar o PATH persistido.

**Resultado da terceira validação Windows (2026-08-10):**
- Execução em novas sessões PowerShell nativas, sem WSL, instalações manuais ou
  administrador.
- `--check-only` terminou com exit `0`.
- `--yes` não produziu saída por mais de 10 minutos e foi interrompido
  manualmente, sem erro explícito ou bloco adicional de comandos pendentes.
- Após nova sessão, `pipx` (`1.16.6`) e Pandoc (`3.7.0.2`) estavam disponíveis;
  `crwl`, Docling, `codebase-memory-mcp` e pytest global continuavam ausentes.
- `.venv\Scripts\pytest.exe` existia, mas `import opencode_config` falhou e
  `pytest -m copilot -q` terminou com 8 erros de coleta.
- `%USERPROFILE%\.copilot\` permaneceu populado corretamente e as 13
  ocorrências de `wsl`/`/mnt/c` estavam somente em documentação/instruções.
- Os seis fluxos não foram executados conforme R1. Como o bootstrap foi
  interrompido durante o setup dos browsers, o comportamento do CLI não foi
  avaliado.
- Diagnóstico isolado concluído: `pipx install crawl4ai` instalou
  `crawl4ai 0.9.2` e criou `crwl.exe` usando Python 3.14. O `crawl4ai-setup`
  falhou ao baixar Chromium e Patchright do CDN do Playwright com
  `SELF_SIGNED_CERT_IN_CHAIN`, repetiu tentativas por cerca de 11 minutos e
  terminou com exit `0` apesar de registrar `Failed to install browsers`.
- O diagnóstico seguinte recebeu `PLAYWRIGHT_DOWNLOAD_HOST` apontando para
  mirror corporativo com rota `/api/`, que estava incorreta.
  O mirror foi alcançado sem erro TLS, mas retornou `404 Not found` para
  `builds/cft/151.0.7922.34/.../chrome-win64.zip` e
  `builds/cft/149.0.7827.55/.../chrome-win64.zip`; o setup novamente registrou
  `Failed to install browsers` e saiu com exit `0`.
- A captura do Artifactory revelou que a URL nativa correta remove `/api/`:
  mirror corporativo com rota nativa, sem `/api/`. Testes
  `HEAD` retornaram `200 OK` e `content-type: application/zip` para os dois
  artefatos. O diagnóstico precisa ser repetido com essa base.
- O bloqueio anterior era a rota incorreta do mirror, não resolução de
  dependências ou incompatibilidade do pacote; AD-2 não precisa ser reaberta.
- O setup também criou backup/migração da base em
  `C:\Users\ur5y\.crawl4ai`; o pacote e seus executáveis ficaram isolados na
  pasta temporária do diagnóstico.
- Nenhum arquivo versionado foi revertido ou editado; as 10 alterações
  intencionais permaneceram.
- Evidências:
  `C:\Users\ur5y\AppData\Local\Temp\opencode-config-task45-validation-20260810-1158`.
- Diagnóstico:
  `C:\Users\ur5y\AppData\Local\Temp\crawl4ai-diagnostic-20260810-140850`.
- Diagnóstico com mirror:
  `C:\Users\ur5y\AppData\Local\Temp\crawl4ai-diagnostic-20260810-144412`.
- Diagnóstico com rota nativa corrigida:
  `C:\Users\ur5y\AppData\Local\Temp\crawl4ai-diagnostic-20260810-150912`.
  Playwright e Patchright concluíram a instalação de Chrome, headless shell,
  FFmpeg e Winldd usando o mirror; não houve erro TLS, 404 ou falha de setup.
- Validação final do bootstrap:
  `C:\Users\ur5y\AppData\Local\Temp\opencode-config-task45-final-20260810-1532`.
  `node 22.14.0` e `pipx 1.16.6` foram detectados, mas `npm`/`npx` não
  estavam disponíveis. Os ambientes pipx foram criados em
  `C:\Users\ur5y\AppData\Local\pipx\pipx\venvs`, com apps expostos em
  `C:\Users\ur5y\.local\bin`; o bootstrap esperava
  `C:\Users\ur5y\AppData\Local\pipx\bin`, fazendo `crawl4ai-setup` falhar por
  comando não encontrado.
- Acceptance criteria permanecem bloqueados por R1: bootstrap sem elevação
  falhou; os seis fluxos, a varredura de comandos proibidos e o pytest não
  foram executados. O adapter Copilot foi populado e o `git status` permaneceu
  inalterado; nenhum commit foi criado.

**Resultado final da validação Windows (2026-08-11):**
- **PASS:** PowerShell nativo, sem WSL, sem administrador, branch
  `master-nova`, checkout `C:\Users\ur5y\Projetos\opencode-config`.
- `--check-only`: exit `0`; `--yes`: exit `0`; nenhum prompt UAC.
- PATH Windows corrigido para preservar ordem do processo, importar PATH do
  usuário e evitar alias `WindowsApps\python.exe`; testes não persistem PATH
  temporário.
- Entry points disponíveis em nova sessão: `crwl`, `crawl4ai-setup`, `docling`,
  `codebase-memory-mcp`, `pandoc`, `playwright`, `opencode-config-check`,
  `opencode-*`, `copilot`, npm e npx.
- Copilot CLI entrou no bootstrap via pacote npm user-space. codebase-memory foi
  fixado em `0.9.0`, cuja instalação Windows concluiu sem o timeout de validação
  do pacote mais recente.
- O relatório Windows registrou Docling 2.119.0, enquanto o WSL usava 2.96.1.
  O wrapper foi corrigido para usar a sintaxe comum sem `convert` e passou a
  exigir artefato não vazio; modelos precisam estar previamente no cache local.
  A revalidação Windows desse contrato ainda está pendente.
- Fluxos reais: `crwl`, codebase discovery com `index_repository --mode fast` e
  `search_graph`, doc-extract offline, md-export, svg-to-image e
  browser-testing: todos exit `0`.
- `pytest tests\bootstrap tests\lib -q`: `72 passed`.
- `pytest -m "unit or tools" -q`: validação Windows anterior registrada como
  `361 passed, 46 deselected`; WSL após a correção: `372 passed, 46
  deselected`.
- `pytest -m "unit or tools or copilot" -q`: `363 passed, 44 deselected`.
- `pytest -m copilot -q`: `2 passed, 405 deselected`.
- `%USERPROFILE%\.copilot\` contém `skills`, `agents`, `default-artifacts` e
  `instructions`; varredura encontrou somente menções documentais a `wsl` ou
  `/mnt/c`, sem comando operacional.
- Evidências: `C:\Users\ur5y\AppData\Local\Temp\opencode-config-task45-final-20260811`.
- CA corporativa foi usada somente em arquivos temporários de ambiente
  (`NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`); nenhuma URL,
  certificado ou bypass TLS foi versionado.

**Revalidação Windows após a correção Docling (2026-08-11):**
- **PASS:** Docling 2.119.0, wrapper `opencode-doc-extract.exe` e forma comum
  sem `convert` validados em PowerShell nativo.
- `sample.md`: `ok:true`, artefato não vazio de 129 bytes.
- `sample.pdf` vazio: `ok:false`, erro explícito de artefato vazio.
- `pytest tests\cli\test_doc_extract.py -q`: `13 passed`.
- `pytest -m "unit or tools or copilot" -q`: `374 passed, 44 deselected`.
- Evidências: diretórios temporários
  `docling-md-validation` e `docling-empty-pdf-validation`.

**Dependencies:** 4.4

**Files likely touched:** `tests/integration/test_copilot.py`, `README.md`

**Estimated scope:** M

---

### Checkpoint: Bootstrap multiplataforma
- [x] Bootstrap zero-admin validado em Windows sem admin e WSL; fluxo Docling
  revalidado nos dois sistemas
- [x] Seleção interativa funcionando; `--yes` e `--check-only` corretos
- [x] Suítes `unit/tools` verdes no WSL e no Windows após a correção Docling
- [ ] Revisão com o humano

---

### Fase 5: Scripts de manutenção → Python

#### Task 5.1: `opencode-skills` — sync de upstream

**Description:** Unificar `scripts/lib/sync-common.sh`,
`scripts/accessibility-audit/sync.sh`, `scripts/addyosmani/sync.sh` e
`scripts/prompt-improver/sync.sh` num único comando com subcomandos, dirigido
pelos metadados de `UPSTREAM.md`. Preservar a regra de ouro: **nunca
sobrescrever `SKILL.md`**.

**Acceptance criteria:**
- [x] `SKILL.md` jamais é sobrescrito pelo sync
- [x] `--yes` e `--check-only` preservados em todos os fluxos
- [x] `UPSTREAM.md` atualizado com novo SHA e data após sync
- [x] Campos `description_lang` / `description_note` preservados

**Verification:**
- [x] `pytest -m unit tests/skills_mgmt/test_sync.py` (porte de
      `accessibility-audit-sync-test.bats` + `addyosmani-sync-test.bats`)
      com repositório git fake

**Dependencies:** 0.2

**Files likely touched:** `src/opencode_config/cli/skills_sync.py`,
`tests/skills_mgmt/test_sync.py`, `scripts/lib/**`, `scripts/*/sync.sh` (removidos)

**Estimated scope:** L — **quebrar em 5.1a (lib comum + `list-updatable`) e
5.1b (os 3 syncs concretos)**

---

#### Task 5.2: `opencode-skills list` / `update`

**Description:** Portar `scripts/skills/list-updatable.sh` (39) e
`scripts/skills/update-upstream-skill.sh` (328) como subcomandos do mesmo
entry point, preservando os status de retorno (`success`,
`already-up-to-date`, `no-clear-update-flow`, `ambiguous-update-flow`) e o
`--dry-run`.

**Acceptance criteria:**
- [x] Todos os status de retorno preservados
- [x] `--dry-run` não altera nada
- [x] `commands/sync-upstream-skills.md` atualizado para os novos comandos

**Verification:**
- [x] `pytest -m unit tests/skills_mgmt/test_update.py` (porte de
      `list-updatable-test.bats` + `update-upstream-skill-test.bats`)

**Dependencies:** 5.1

**Files likely touched:** `src/opencode_config/cli/skills_sync.py`,
`tests/skills_mgmt/test_update.py`, `commands/sync-upstream-skills.md`,
`scripts/skills/**` (removido)

**Estimated scope:** M

---

#### Task 5.3: `opencode-scaffold-mapa`

**Description:** Portar `scripts/mapa-produto/scaffold.sh` para Python. É o
script com a maior suíte de testes do repo (`scaffold-test.bats`, 450 linhas) —
tratar essa suíte como especificação executável.

**Acceptance criteria:**
- [x] Estrutura de diretórios e arquivos gerada idêntica à do script bash
- [x] Comportamento de idempotência e de sobrescrita preservado
- [x] Os 450 linhas de spec BATS têm equivalente pytest

**Verification:**
- [x] `pytest -m unit tests/scaffold/test_mapa_produto.py`
- [x] Diff de árvore gerada: bash vs Python, num diretório temporário

**Dependencies:** 0.2

**Files likely touched:** `src/opencode_config/cli/scaffold_mapa.py`,
`tests/scaffold/test_mapa_produto.py`, `scripts/mapa-produto/**` (removido)

**Estimated scope:** L

**Skills:** `tests-as-spec` (a suíte de 450 linhas é a spec)

---

### Checkpoint: Manutenção migrada
- [x] Nenhum `.sh` restante em `scripts/` além dos 2 entrypoints
- [x] `pytest -m unit` verde (304 testes aprovados)
- [x] Sync de uma skill upstream real executado com sucesso
      (`accessibility-audit`, commit `75c558b7`)
- [ ] Revisão com o humano

---

### Fase 6: Aposentadoria do BATS e do Makefile

#### Task 6.1: Migrar as suítes restantes para pytest

**Description:** Portar as suítes ainda em BATS: `tests/agents/` (4 arquivos,
444 linhas), `tests/integration/` (agents, commands, prompts,
skills-activation, docker) e `tests/scripts/bootstrap_repo/` (repo-state,
repo-structure, chrondb-fix). Converter a orquestração do container Docker
(`container-test-opencode.sh`) em fixture session-scoped e o
`entrypoint.sh` em `entrypoint.py` (adicionando `python3` ao Dockerfile).

**Acceptance criteria:**
- [x] Nenhum arquivo `.bats` no repo
- [x] Container de teste sobe e desce por fixture, com teardown garantido
- [x] Guarda de `OPENCODE_TEST_MODEL` vira `pytest.fail` com a mesma orientação
- [x] Cobertura equivalente — nenhum teste perdido na conversão

**Verification:**
- [ ] `pytest -m opencode` verde no WSL — bloqueado neste ambiente:
      serviço OpenCode/Docker e `OPENCODE_TEST_MODEL` não estão disponíveis
- [x] Comparar contagem de testes antes/depois: 160 BATS → 160 pytest

**Dependencies:** fase 5 completa

**Files likely touched:** `tests/**` (toda a árvore),
`tests/integration/docker/Dockerfile`, `entrypoint.sh` → `entrypoint.py`

**Estimated scope:** L — **quebrar por diretório de teste**

**Skills:** `tests-as-spec`, `debugging-and-error-recovery`

---

#### Task 6.2: Remover Makefile, BATS e suas dependências

**Description:** Remover o `Makefile`, a instalação de `bats`, `bats-support`,
`bats-assert`, `bats-file` do bootstrap, e o bloco `BATS_LIB_PATH` do
`~/.bashrc` (com limpeza idempotente do bloco legado).

**Acceptance criteria:**
- [x] `Makefile` removido
- [x] Bootstrap não instala mais nada de BATS
- [x] Bloco `BATS_LIB_PATH` removido do `~/.bashrc` pelo bootstrap
- [x] `grep -ri "bats"` retorna apenas `plan/` e `docs/adr/`

**Verification:**
- [x] `pytest -m "unit or tools"` verde
- [x] Bootstrap num `HOME` limpo não cria `~/.local/lib/bats`

**Dependencies:** 6.1

**Files likely touched:** `Makefile` (removido),
`src/opencode_config/bootstrap/registry.py`,
`src/opencode_config/adapters/opencode.py`, `README.md`

**Estimated scope:** S

---

#### Task 6.3: Documentação final e ADRs

**Description:** Revisão final de `README.md`, `AGENTS.md`,
`.github/copilot-specific.instructions.md`, `agents/default-artifacts/doc-readme.md`,
`docs/workflow-*.md` e `scripts/bootstrap_repo/README.md`. Consolidar os ADRs.
Atualizar as regras do `AGENTS.md` que deixaram de valer: framework de testes
(BATS→pytest), comando de teste (`make test-opencode`→`pytest -m`), estrutura de
scripts, sincronização de adapters `.sh`/`.ps1`, e a regra de line endings LF
(que era motivada por `.bats`/bash no WSL).

**Acceptance criteria:**
- [x] `AGENTS.md` reflete o repo pós-migração, sem regra órfã
- [x] README documenta bootstrap Linux **e** Windows, com a estratégia zero-admin
- [x] Seção de dependências do README bate com o registro de AD-10
- [ ] `aws --version` funciona nos dois SOs após bootstrap, sem elevação (AD-13);
      WSL passou, Windows pendente
- [x] ADRs cobrem AD-1..AD-13
- [ ] Nenhuma linha de MD passa de 120 colunas; a documentação operacional
      alterada está dentro do limite, mas skills externas antigas ainda têm
      linhas longas

**Verification:**
- [x] Leitura completa dos docs por agente revisor, comparando com o repo;
      nenhum achado significativo restante
- [x] `tests/docs/` não existe; a suíte WSL `pytest -m "unit or tools"` passou

**Dependencies:** 6.2

**Files likely touched:** `README.md`, `AGENTS.md`,
`.github/copilot-specific.instructions.md`, `docs/**`,
`agents/**`, `scripts/bootstrap_repo/README.md`

**Estimated scope:** M

**Skills:** `documentation-and-adrs`, `code-review-and-quality`

---

### Checkpoint: Migração completa
- [x] Zero `.sh` no repo além dos 2 entrypoints de bootstrap; zero `.ps1` além de 1
- [x] Zero `.bats`; zero `Makefile`
- [x] Zero MCP local; zero Docker para crawl4ai
- [ ] `pytest -m "unit or tools or opencode"` verde no WSL — OpenCode bloqueado
- [ ] `pytest -m "unit or tools or copilot"` verde no Windows
- [ ] Bootstrap zero-admin validado nos dois SOs
- [x] Documentação consistente com o estado do repo — revisão final aprovada
- [ ] Pronto para revisão final

**Estado Windows:** a validação final de 2026-08-10 falhou antes dos fluxos de
skill por dois defeitos do bootstrap: apps pipx expostos em diretório diferente
do PATH gerenciado e ausência de verificação de `npm`/`npx` quando `node` está
presente. O mirror de browsers já foi validado isoladamente; R1 permanece
bloqueado até a correção e nova execução.

---

## Risks and Mitigations

| # | Risco | Impacto | Mitigação |
|---|---|---|---|
| R1 | `crwl` local se comporta diferente do container (anti-bot, stealth, rate limit) | **Alto** | Ver nota R1 |
| R2 | `crawl4ai` tem 54 deps; instalação pesada/frágil no Windows | **Alto** | Ver nota R2 |
| R3 | Playwright renderiza SVG diferente do `resvg` | Médio | Task 2.3 compara saídas antes de remover |
| R4 | Conversão de 4.608 linhas de BATS perde cobertura | **Alto** | Ver nota R4 |
| R5 | Windows corporativo bloqueia download ou execução de `.ps1` | **Alto** | Ver nota R5 |
| R6 | Escrita em PATH conflita com política corporativa | Médio | Bloco marcado idempotente; `--check-only` |
| R7 | `pipx install --editable .` diverge entre SOs | Médio | Validar na Task 0.1 nos dois ambientes |
| R8 | Repo em estado misto por período longo | Médio | Fatias verticais + checkpoint por fase |
| R9 | Perda de histórico git em move/rename | Baixo | `git mv` obrigatório, sem delete+create |
| R10 | `codebase-memory-mcp cli` mais lento que MCP | Médio | Ver nota R10 |

**Notas de mitigação**

- **R1** — Validar na Task 1.4 com URLs reais (incluindo sites com JS e
  anti-bot) antes de deletar o container. Manter a imagem local disponível até
  o checkpoint da fase 1 permitir rollback barato.
- **R2** — `pipx install crawl4ai` foi reproduzido isoladamente no Windows
  com sucesso (`crawl4ai 0.9.2`, Python 3.14); o risco de resolução das
  dependências não foi confirmado.
- **R4** — `tests-as-spec` é obrigatório: cada `.bats` vira spec antes de
  virar pytest. Comparar contagem de asserções por suíte, antes e depois.
- **R5** — A primeira configuração usou `/api/` indevidamente e recebeu
  `404 Not found`; a rota nativa sem `/api/` instalou com sucesso todos os
  browsers no diagnóstico isolado. Repetir no bootstrap completo; não usar
  bypass TLS inseguro.
- **R10** — Medir latência na Task 1.5. O CLI sobe um processo por chamada,
  sem o estado persistente do servidor MCP. Se o custo for proibitivo,
  avaliar o modo servidor local do próprio binário.

## Open Questions

As quatro questões levantadas foram resolvidas — três por investigação e a
Q1 por confirmação do humano. A validação operacional do Windows permanece
pendente e não é tratada como nova questão de arquitetura.

- **Q1 — RESOLVIDA.** O humano confirmou ter acesso a uma máquina Windows sem
  privilégio de administrador para executar a validação da Task 4.5 e pediu
  que todas as validações Windows fiquem para a instalação final. São
  exatamente essas máquinas que motivaram a estratégia zero-admin de AD-9.
- **Q2 — RESOLVIDA.** `auto_index` é config do binário
  (`codebase-memory-mcp config list` → `auto_index=true`,
  `auto_index_limit=50000`), não do transporte MCP. Continua válido no modo
  CLI. **Ação:** manter a configuração no bootstrap; remover apenas o
  `codebase-memory-mcp install -y`, que instalava skills MCP.
- **Q3 — RESOLVIDA.** `tests/scripts/doctree/` (2 arquivos, 159 linhas) testa
  `scripts/doctree/install.sh`, que **não existe** no repo. Não há nenhuma
  outra referência a `doctree`. Suíte órfã. **Ação:** remover na Task 1.1
  (limpeza), sem equivalente pytest.
- **Q4 — RESOLVIDA.** Menções a MCP fora dos docs principais:
  `agents/curador-produto-editor.md` (l.158, 245, 305) e
  `docs/workflow-curadoria.md` (l.178, 336). São referências a
  *codebase-memory como ferramenta*, não à sintaxe MCP — exceto
  `curador-produto-editor.md:245` ("Graphify, MCP server"). **Ação:** incluir
  os dois arquivos na Task 1.5, respeitando a regra do `AGENTS.md` de manter
  agentes e workflows sincronizados.

Todas as questões levantadas foram resolvidas:

## Varredura de Ferramentas Externas (concluída)

Após identificar que o AWS CLI havia escapado do inventário original, foi feita
uma varredura sistemática de `agents/` e `skills/` atrás de outras ferramentas
externas invocadas diretamente por agentes — classe de dependência que a
varredura inicial (focada em MCP e scripts) não cobria.

**Resultado: o AWS CLI era a única lacuna real.** Nenhuma segunda foi
encontrada.

As demais ferramentas detectadas — `semgrep`, `trivy`, `gitleaks`, `axe`,
`pa11y`, `lighthouse`, `sqlfluff`, `alembic`, `flyway`, `liquibase`, `eslint`,
`prettier`, `ruff`, `mypy` — são **harness do projeto-alvo**, não dependências
do `opencode-config`. Isso é explícito por design:

- `skills/harness-catalog/SKILL.md`: "Não são regras obrigatórias. O harness
  efetivo de cada agente é definido no /doc/README.md de cada projeto."
- `agents/sec.md:197`: "conforme stack"
- `agents/front.md:265`: "usando ferramentas do projeto"
- `agents/dba.md:43`: "por conta própria"

Corretamente fora do escopo do bootstrap — não devem entrar no registro de
AD-9/AD-10.

**Dependências de nível de repo, todas já cobertas:** `docling` (doc-extract),
`pandoc` (md-export), Playwright (browser-testing e, sob AD-9, svg-to-image),
`crwl` (web-research + doc-extract), `aws` (aws-analista + as duas skills AWS,
agora endereçado por AD-13). Os scripts do repo exigem apenas `git` e
`python3`.
