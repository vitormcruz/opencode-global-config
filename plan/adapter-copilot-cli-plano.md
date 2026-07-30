# Plano de Reestruturação — Adapter Copilot CLI

## 0. Premissas

### Plataformas suportadas

| Plataforma | Status | Modo de sessão |
|---|---|---|
| **OpenCode** | Suportada | Stateful (sessão persistente nativa) |
| **Copilot CLI** | Suportada | Stateful (`copilot --resume`,
  `~/.copilot/session-state/{sessionId}/`) |
| **VS Code Copilot Chat** | **Descartada** | Stateless por design em
  `runSubagent` — inviabiliza orquestração multi-agente |

### Por que VS Code Chat sai

`runSubagent` no VS Code Copilot Chat é stateless: cada
invocação é isolada, sem continuidade de sessão. Isso
impede o modelo do `devflow` (orquestrador que spawna
agentes e espera retomada de contexto). Fontes:
- https://zenn.dev/openjny/articles/2619050ec7f167
- Docs oficiais do VS Code

### Copilot CLI — capacidades confirmadas

- **Sessão persistente**: `copilot --continue`,
  `copilot --resume SESSION-ID`, `/resume`. Persiste
  conversa, tool results, `plan.md`, artefatos em
  `~/.copilot/session-state/{sessionId}/`.
- **Infinite sessions**: compaction automático com
  `infiniteSessions.enabled: true`.
- **Subagentes**: `/fleet` para paralelização.
  Custom agents em `.github/agents/` ou
  `~/.copilot/agents/`. `task(agent_type=...)` via
  SDK.
- **Skills**: padrão agentskills.io. Descoberta
  automática em `~/.copilot/skills/`,
  `.github/skills/`, `.claude/skills/`,
  `.agents/skills/`. SKILL.md com frontmatter
  (`name`, `description`).
- **MCP**: nativo + por agente (`mcp-servers` no
  frontmatter).
- **Tools**: aliases (`execute`, `read`, `edit`,
  `search`, `agent`, `web`, `todo`).

### Decisoes ja tomadas

1. VS Code Copilot Chat descartado.
2. Frontmatter OpenCode e canonico; adapter traduz
   para Copilot CLI no bootstrap.

---

## 1. Decisoes de Arquitetura

### 1.1. Frontmatter de agentes — traducao canonica

**Decisao:** o frontmatter OpenCode e a fonte de
verdade. O adapter de bootstrap converte para o formato
Copilot CLI (`.agent.md`) no momento da sincronizacao.

#### Mapeamento de campos

| Campo OpenCode | Campo Copilot CLI | Conversao |
|---|---|---|
| `description` | `description` | Direto |
| `mode: primary` | *(omitido)* | Default do Copilot CLI |
| `mode: subagent` | `user-invocable: false` | Impede selecao manual |
| `temperature` | *(descartado)* | Sem equivalente no
  frontmatter (.agent.md). `reasoningEffort` so existe
  no SDK SessionConfig, nao no YAML do agente. |
| `permission.edit: allow` | `tools` inclui `edit` | Adiciona alias |
| `permission.edit: deny` | `tools` exclui `edit` | Remove alias |
| `permission.bash: allow` | `tools` inclui `execute` | Adiciona alias |
| `permission.bash: deny` | `tools` exclui `execute` | Remove alias |
| `permission.webfetch: allow` | `tools` inclui `web` | Adiciona alias |
| `permission.websearch: allow` | `tools` inclui `web` | Adiciona alias |
| `permission.task: { X: allow }` | `tools` inclui `agent` | Permite spawnar subagentes |
| `permission.task: { "*": deny }` | `tools` exclui `agent` | Impede spawn |

#### Tool aliases do Copilot CLI (referencia)

| Alias | Compativeis | Proposito |
|---|---|---|
| `execute` | `shell`, `Bash`, `powershell` | Executar comandos |
| `read` | `Read`, `NotebookRead` | Ler arquivos |
| `edit` | `Edit`, `Write`, `MultiEdit` | Editar arquivos |
| `search` | `Grep`, `Glob` | Buscar arquivos/texto |
| `agent` | `custom-agent`, `Task` | Invocar subagente |
| `web` | `WebSearch`, `WebFetch` | Web search/fetch |
| `todo` | `TodoWrite` | Task lists |

#### Exemplo de conversao

**OpenCode (fonte):**

```yaml
---
description: >
  Engenheiro de Software — planeja implementacao
mode: primary
temperature: 0.2
permission:
  edit: allow
  bash: allow
  webfetch: deny
  websearch: deny
  task:
    "*": deny
---
```

**Copilot CLI (gerado):**

```yaml
---
description: >
  Engenheiro de Software — planeja implementacao
tools: ["read", "edit", "execute", "search"]
---
```

Nota: `web` e `agent` omitidos (deny). `read` e
`search` adicionados como default para qualquer agente
com `edit: allow` (precisa ler para editar).

#### Arquivos afetados

- `scripts/bootstrap_repo/copilot-sync.ps1` — funcao
  `Strip-AgentFrontmatter` substituida por
  `Convert-AgentFrontmatter` que gera frontmatter
  Copilot CLI completo
- `scripts/bootstrap_repo/wsl-copilot-sync.sh` —
  funcao `strip_agent_frontmatter` substituida por
  `convert_agent_frontmatter` equivalente
- Destino: `.github/agents/*.agent.md` (repo-level)
  ou `~/.copilot/agents/*.agent.md` (user-level)

#### Riscos

- Campos novos no frontmatter OpenCode exigem update
  do adapter (acoplamento bidirecional).
- `infer` esta marcado como **retired** no Copilot
  CLI — usar `disable-model-invocation` +
  `user-invocable` em vez disso.

### 1.2. Interacao agente-humano — deferida

**Decisao:** a questao de comunicacao agente↔humano
em modo orquestrado esta deferida para o plano
`plan/devflow-mediador-comunicacao.md`.

**Contexto:** a premissa 4 do workflow atual permite
que qualquer agente consulte o humano diretamente.
No Copilot CLI, subagentes sao isolados (nao
interagem com humano). O plano do mediador resolve
isso de forma generica para todas as plataformas:
o devflow passa a intermediar TODA comunicacao
agente↔humano, eliminando a necessidade de agentes
terem tool `ask` (OpenCode) ou serem primarios
(VS Code, descartado).

**Impacto neste plano:** as referencias a "VS Code"
e `runSubagent` nos agentes e workflows serao
substituidas por "Copilot CLI" com a semantica do
mediador (agente retorna perguntas ao devflow, nao
ao humano). A execucao deste plano nao depende da
resolucao do mediador, mas as mudancas nos prompts
 do devflow e workflows devem ser coordenadas.

### 1.3. Politica de sessao e modelo por fase

**Decisao:** sessoes sao estruturadas por fase do
workflow. Intra-fase, a sessao e mantida (resume).
Inter-fase, sessao nova e criada.

#### Estrutura do Session ID

```
{workflowId}-{fase}-{agente}
```

Exemplo: `feat-login-PLANEJAMENTO-eng-software`

#### Comportamento por cenario

| Cenario | Acao | Mecanismo |
|---|---|---|
| Agente conclui fase | Nova sessao para proxima fase | `createSession(sessionId novo)` |
| Agente retorna pergunta ao devflow | Mesma sessao preservada | `resumeSession(sessionId)` |
| Devflow re-spawna agente na mesma fase | Mesma sessao | `resumeSession(sessionId)` |
| Mudanca de fase | Nova sessao | `createSession(sessionId novo)` |
| Gate de refatoracao (volta a fase 3) | Nova sessao para fase anterior | `createSession(sessionId novo)` |

#### Modelo por fase

O modelo e especificado ao criar a sessao da fase
(SessionConfig `model` no SDK, ou `/model` na CLI
antes do spawn). O frontmatter do agente nao define
`model` fixo — o modelo e controlado pelo devflow
por fase, conforme mapa registrado no arquivo de
planejamento.

**OpenCode:** devflow para e pede ao humano para
trocar modelo antes de cada fase com modelo diferente.

**Copilot CLI:** devflow instrui humano a usar
`/model` antes de cada fase, ou o modelo e definido
na criacao da sessao via SDK.

#### Persistencia de contexto

| Plataforma | Intra-fase | Inter-fase |
|---|---|---|
| OpenCode | `task_id` (mesma sessao de subagente) | Instancia nova |
| Copilot CLI | `resumeSession(sessionId)` | `createSession(sessionId novo)` |

#### Arquivos afetados

- `agents/devflow.md` — secao "Selecao de modelo por
  fase": substituir "VS Code" por "Copilot CLI" e
  adicionar politica de sessao
- `docs/workflow-agentes-dev.md` — premissa 7:
  atualizar aplicacao por plataforma
- `plan/devflow-mediador-comunicacao.md` — secao 4.1:
  alinhar com politica de sessao definida aqui

### 1.4. Destinos do bootstrap e artefatos sem equivalente

**Decisao:** os scripts de bootstrap devem destinar
artefatos para paths nativos do Copilot CLI, eliminando
todos os destinos VS Code.

#### Mapeamento de destinos

| Artefato | Destino antigo (VS Code) | Destino novo (Copilot CLI) |
|---|---|---|
| Skills | `~/.copilot/skills/` | `~/.copilot/skills/` (sem mudanca) |
| Instructions | `~/.copilot/instructions/` | `~/.copilot/instructions/` (sem mudanca) |
| Agents | `%APPDATA%/Code/User/prompts/*.agent.md` e `~/.vscode-server/data/User/prompts/*.agent.md` | `~/.copilot/agents/*.agent.md` |
| Commands | `%APPDATA%/Code/User/prompts/*.prompt.md` | Skills com description curta |
| Default-artifacts | `%APPDATA%/Code/User/prompts/default-artifacts/` | `.github/agents/default-artifacts/` |
| MCP (VS Code) | `%APPDATA%/Code/User/mcp.json` e `~/.vscode-server/data/User/mcp.json` | **Removido** (VS Code descartado) |
| MCP CLI globais | `~/.config/mcp/servers.json` | `~/.config/mcp/servers.json` (sem mudanca) |

#### Commands → Skills (3 casos)

| Command | Skill resultante | Description (curta) |
|---|---|---|
| `index-codebase.md` | `skills/index-codebase/SKILL.md` | "Indexa repo no codebase-memory. Ative quando humano pedir index codebase ou indexar repositorio." |
| `bench-indexing.md` | `skills/bench-indexing/SKILL.md` | "Benchmark de indexacao codebase-memory. Ative quando humano pedir bench indexing." |
| `sync-upstream-skills.md` | `skills/sync-upstream-skills/SKILL.md` | "Sincroniza skills com upstream. Ative quando humano pedir sync upstream skills." |

**Principio:** descriptions curtas e especificas para
evitar ativacao inadvertida por agentes. Copilot CLI
so carrega skill quando relevante ao prompt.

#### Default-artifacts

Os arquivos permanecem em `agents/default-artifacts/`
no repo. O script de bootstrap os copia para
`.github/agents/default-artifacts/` no destino,
junto com os `.agent.md`. O agente
`curador-produto-editor` le via tool `read`
(caminho relativo ao agente).

#### Mudancas nos scripts

**`copilot-sync.ps1` (Windows):**
- `$PromptsDir` muda de `%APPDATA%\Code\User\prompts`
  para `%USERPROFILE%\.copilot\agents`
- `$McpJson` removido (VS Code descartado)
- `Sync-Commands` substituido por `Sync-CommandsAsSkills`
- `Sync-DefaultArtifacts` destina para
  `.copilot\agents\default-artifacts\`
- `Sync-Mcp` removida (VS Code `mcp.json`)
- `Strip-AgentFrontmatter` substituida por
  `Convert-AgentFrontmatter` (decisao 1.1)
- `detect_windows_targets` removido

**`wsl-copilot-sync.sh` (WSL):**
- `prompts_dir` muda de `~/.vscode-server/data/User/prompts`
  para `~/.copilot/agents`
- `mcp_json` removido (VS Code `mcp.json`)
- `windows_prompts_dir` e `windows_code_user_dir` removidos
- `sync_commands` substituido por `sync_commands_as_skills`
- `sync_default_artifacts` destina para
  `~/.copilot/agents/default-artifacts/`
- `sync_mcp` removida (VS Code)
- `strip_agent_frontmatter` substituida por
  `convert_agent_frontmatter` (decisao 1.1)
- `detect_windows_targets` removida

**`AGENTS.md` / `README.md`:**
- Remover referencias a VS Code Windows/Server
- Atualizar tabela de artefatos sincronizados

### 1.5. Skills — compatibilidade agentskills.io

**Decisao:** todas as skills do repo devem seguir
o padrao agentskills.io (name + description required)
para compatibilidade nativa com Copilot CLI.

#### Problemas encontrados

| Skill | Problema |
|---|---|
| `browser-testing` | Sem frontmatter YAML — falha no Copilot CLI |
| Diversas | Descriptions com triggers OpenCode (redundantes mas inofensivos) |

#### Acoes no bootstrap

`Adapt-SkillForCopilot` (copilot-cli-adapter.ps1) e
`rewrite_skill_script_refs` (copilot-cli-adapter.sh) sao
estendidos para:

1. **Adicionar frontmatter** se ausente — gera `name`
   do nome do diretorio e `description` do primeiro
   paragrafo do SKILL.md
2. **Validar name** — deve bater com nome do diretorio,
   lowercase com hyphens, max 64 chars

#### Acao no repo

- `skills/browser-testing/SKILL.md`: adicionar
  frontmatter com `name: browser-testing` e
  `description` apropriada

#### Triggers do OpenCode em descriptions

Nao sao removidos — sao inofensivos no Copilot CLI
(matching semantico nao e afetado). Manter para
preservar ativacao no OpenCode.

### 1.6. Reorganizacao do repo — pasta adapters/

**Decisao:** criar pasta `adapters/` com subpastas
por plataforma. Todas as plataformas passam por
adapter — OpenCode deixa de ser privilegiado.

#### Estrutura proposta

```
opencode-global-config/
├── agents/              # fonte canonica (frontmatter OpenCode)
│   ├── eng-software.md
│   ├── devflow.md
│   └── default-artifacts/
├── skills/              # fonte canonica (agentskills.io)
├── commands/            # fonte canonica (slash commands)
├── docs/                # workflows (genericos)
├── adapters/
│   ├── opencode/
│   │   ├── opencode-adapter.sh  # cria symlinks ~/.config/opencode
│   │   └── README.md            # como usar
│   └── copilot-cli/
│       ├── copilot-cli-adapter.sh   # copia+transforma p/ ~/.copilot/
│       ├── copilot-cli-adapter.ps1  # versao Windows
│       └── README.md                # como usar
├── scripts/
│   └── bootstrap_repo/
│       ├── configurar-repo.sh  # orquestrador (chama adapters)
│       └── wsl-install-deps.sh
├── tests/
│   ├── agents/          # testa fonte canonica
│   ├── adapters/        # testa output por plataforma
│   │   ├── opencode/
│   │   │   └── opencode-adapter-test.bats
│   │   └── copilot-cli/
│   │       ├── copilot-cli-adapter-test.bats
│   │       └── copilot-cli-adapter-ps1-test.bats
│   └── integration/     # smoke tests por plataforma
└── opencode.json        # config OpenCode (mantida)
```

#### Migracao dos scripts existentes

| Script atual | Destino |
|---|---|
| `scripts/bootstrap_repo/opencode-link.sh` | `adapters/opencode/opencode-adapter.sh` |
| `scripts/bootstrap_repo/copilot-sync.ps1` | `adapters/copilot-cli/copilot-cli-adapter.ps1` |
| `scripts/bootstrap_repo/wsl-copilot-sync.sh` | `adapters/copilot-cli/copilot-cli-adapter.sh` |

#### Principio

- **Fonte canonica** no raiz (agents, skills, commands, docs)
- **Adapters** transformam fonte para cada plataforma
- **Nenhum agente/skill/doc** contem logica de plataforma
- **Bootstrap** (`configurar-repo.sh`) orquestra adapters

### 1.7. Estrategia de testes em camadas

**Decisao:** testes organizados em tres camadas.

#### Camada 1: Fonte canonica

Testa que agentes, skills e docs no raiz estao
corretos independentemente de plataforma.

| Teste | O que valida |
|---|---|
| `tests/agents/*.bats` | Frontmatter canonico (campos OpenCode), conteudo, consistencia com workflows |
| `tests/skills/*.bats` | SKILL.md com name+description (agentskills.io), conteudo |

Mantidos do estado atual. Sem mudanca.

#### Camada 2: Adapters

Testa que cada adapter gera output correto para
sua plataforma. Usa temp dirs para isolar.

| Teste | O que valida |
|---|---|
| `tests/adapters/opencode-test.bats` | Symlinks criados corretamente, destinos corretos |
| `tests/adapters/copilot-cli-test.bats` | Frontmatter convertido (tools, description), `.agent.md` gerados, skills compativeis, commands→skills, default-artifacts copiados, MCP VS Code removido |

**Novos.** Espelham `tests/scripts/bootstrap_repo/` mas
focam no output do adapter, nao no script.

#### Camada 3: Integracao

Smoke tests que dependem da plataforma instalada.

| Teste | O que valida |
|---|---|
| `tests/integration/copilot-cli-test.bats` | `copilot --help`, MCP wrapper, agents carregados |
| `tests/integration/opencode-test.bats` | `opencode --help`, agents carregados |

Renomeados de `tests/copilot-int-test/` e
`tests/opencode-int-test/` para `tests/integration/`.

---

## 2. Checklist de Mudancas

### 2.1. Nova estrutura de diretorios

| Acao | Detalhe |
|---|---|
| Criar `adapters/opencode/` | Mover `opencode-link.sh` para ca |
| Criar `adapters/copilot-cli/` | Mover `copilot-sync.ps1` e `wsl-copilot-sync.sh` |
| Renomear `tests/copilot-int-test/` | Para `tests/integration/` |
| Renomear `tests/opencode-int-test/` | Para `tests/integration/` |
| Criar `tests/adapters/opencode/` | Teste do adapter OpenCode |
| Criar `tests/adapters/copilot-cli/` | Testes do adapter Copilot CLI |

### 2.2. `adapters/copilot-cli/copilot-cli-adapter.sh` (ex-wsl-copilot-sync.sh)

| Mudanca | Decisao |
|---|---|
| `strip_agent_frontmatter` → `convert_agent_frontmatter` | 1.1 |
| Destino agents: `~/.copilot/agents/` | 1.4 |
| `sync_commands` → `sync_commands_as_skills` | 1.4 |
| Default-artifacts → `~/.copilot/agents/default-artifacts/` | 1.4 |
| `sync_mcp` (VS Code) removida | 1.4 |
| `detect_windows_targets` removida | 1.4 |
| `Adapt-SkillForCopilot` estendida (frontmatter) | 1.5 |

### 2.3. `adapters/copilot-cli/copilot-cli-adapter.ps1` (ex-copilot-sync.ps1)

Mesmas mudancas do copilot-cli-adapter.sh, em PowerShell.

### 2.4. `adapters/opencode/opencode-adapter.sh` (ex-opencode-link.sh)

| Mudanca | Detalhe |
|---|---|
| Sem transformacao de agents | OpenCode le diretamente |
| Symlinks de `skills/`, `commands/`, `opencode.json` | Ja existe |
| Remover referencias a VS Code | Limpeza |

### 2.5. `agents/devflow.md`

| Linha | Mudanca | Decisao |
|---|---|---|
| 154 | "VS Code: passe model" → "Copilot CLI: use /model ou defina na sessao" | 1.3 |
| Nova secao | Politica de sessao por fase | 1.3 |
| Governanca | Atualizar premissa sobre interacao humano | 1.2 (deferida) |

### 2.6. `docs/workflow-agentes-dev.md`

| Linha | Mudanca | Decisao |
|---|---|---|
| 221 | "VS Code" → "Copilot CLI" | 1.3 |
| 851-862 | Tabela interacao: remover VS Code, atualizar Copilot CLI | 1.2 (deferida) |
| Premissa 7 | Atualizar aplicacao por plataforma | 1.3 |

### 2.7. `README.md`

| Secao | Mudanca |
|---|---|
| "VS Code Server (WSL)" | Remover ou renomear para "Copilot CLI (WSL)" |
| "VS Code Windows" | Remover |
| Tabela artefatos | Atualizar com nova estrutura adapters/ |
| Bootstrap | Documentar `adapters/` |

### 2.8. `skills/browser-testing/SKILL.md`

| Mudanca | Decisao |
|---|---|
| Adicionar frontmatter YAML (name + description) | 1.5 |

### 2.9. `commands/*.md` → `skills/` (no adapter)

| Command | Skill gerada pelo adapter | Decisao |
|---|---|---|
| `commands/index-codebase.md` | `skills/index-codebase/SKILL.md` | 1.4 |
| `commands/bench-indexing.md` | `skills/bench-indexing/SKILL.md` | 1.4 |
| `commands/sync-upstream-skills.md` | `skills/sync-upstream-skills/SKILL.md` | 1.4 |

Nota: os commands permanecem no repo como fonte canonica.
O adapter Copilot CLI os converte para skills no destino.

## 3. Mecanismo de Adapter

Cada adapter e um script que:

1. Le a **fonte canonica** do repo (agents, skills, commands, docs)
2. Aplica **transformacoes** especificas da plataforma
3. Escreve/copiam/linka para os **destinos** da plataforma

### Fluxo generico

```
Fonte canonica (repo)
  │
  ├── adapters/opencode/opencode-adapter.sh
  │     └── Cria symlinks ~/.config/opencode/ → repo
  │         (sem transformacao — OpenCode le nativo)
  │
  └── adapters/copilot-cli/copilot-cli-adapter.sh (.ps1)
        ├── Converte frontmatter (decisao 1.1)
        ├── Copia agents → ~/.copilot/agents/*.agent.md
        ├── Converte commands → skills (decisao 1.4)
        ├── Copia default-artifacts → ~/.copilot/agents/
        ├── Copia skills → ~/.copilot/skills/
        ├── Adiciona frontmatter skills se ausente (decisao 1.5)
        └── Copia instructions → ~/.copilot/instructions/
```

### Quando rodar cada adapter

| Adapter | Trigger |
|---|---|
| OpenCode | `configurar-repo.sh --yes` ou `adapters/opencode/opencode-adapter.sh` |
| Copilot CLI | `configurar-repo.sh --yes` ou `adapters/copilot-cli/copilot-cli-adapter.sh` |
| Ambos | `configurar-repo.sh --yes` (default) |

### Variaveis de ambiente para skip

| Variavel | Efeito |
|---|---|
| `OPENCODE_SKIP_OPENCODE_ADAPTER=1` | Pula adapter OpenCode |
| `OPENCODE_SKIP_COPILOT_ADAPTER=1` | Pula adapter Copilot CLI |

(Substituem `OPENCODE_SKIP_LINKS` e `OPENCODE_SKIP_COPILOT_SYNC` atuais.)

## 4. Contrato Abstrato

Operacoes que cada adapter deve implementar:

| Operacao | OpenCode | Copilot CLI |
|---|---|---|
| `syncAgents` | Symlink `agents/*.md` | Copia + converte frontmatter → `.agent.md` |
| `syncSkills` | Symlink `skills/*/` | Copia + adiciona frontmatter se ausente |
| `syncCommands` | Symlink `commands/*.md` | Converte → `skills/` com description curta |
| `syncDefaultArtifacts` | Symlink `agents/default-artifacts/` | Copia → `~/.copilot/agents/default-artifacts/` |
| `syncInstructions` | N/A (via AGENTS.md) | Copia → `~/.copilot/instructions/` |
| `syncMcp` | Symlink `opencode.json` | N/A (mantido em `~/.config/mcp/servers.json`) |
| `detectPlatform` | Verifica `opencode` no PATH | Verifica `copilot` no PATH |

## 5. Riscos

| Risco | Mitigacao |
|---|---|
| Frontmatter OpenCode muda e adapter Copilot quebra | Testes de adapter (camada 2) validam output |
| Copilot CLI muda formato `.agent.md` | Monitorar releases; adapter isolado |
| `infer` deprecated → `disable-model-invocation` | Adapter usa campos nao-retired (decisao 1.1) |
| Skills com description > 1024 chars no futuro | Adapter valida e trunca se necessario |
| Migracao de usuarios legados | Secao 7 com passo a passo |
| `devflow-mediador` nao implementado ainda | Decisao 1.2 deferida; referencias VS Code substituidas por Copilot CLI |

## 6. Testes

### 6.1. Camada 1 — Fonte canonica (existem)

- `tests/agents/*.bats` — mantidos
- `tests/skills/*.bats` — mantidos
- `tests/docs/*.bats` — mantidos

### 6.2. Camada 2 — Adapters (novos)

| Teste | Valida |
|---|---|
| `tests/adapters/opencode/opencode-adapter-test.bats` | Symlinks criados corretamente, destinos corretos |
| `tests/adapters/copilot-cli/copilot-cli-adapter-test.bats` | Frontmatter convertido, `.agent.md` gerados, skills compativeis, commands→skills, default-artifacts |
| `tests/adapters/copilot-cli/copilot-cli-adapter-ps1-test.bats` | Mesmas validacoes, versao PowerShell |

Estrategia: rodar adapter com `$DestRoot` (param ja
existente nos scripts) apontando para temp dir.
Validar estrutura e conteudo do output.

### 6.3. Camada 3 — Integracao (renomeados)

| Teste | Valida |
|---|---|
| `tests/integration/copilot-cli-test.bats` | `copilot --help`, MCP wrapper, agents carregados |
| `tests/integration/opencode-test.bats` | `opencode --help`, agents carregados |

### 6.4. Migracao dos testes existentes

| Origem | Destino | Mudanca |
|---|---|---|
| `tests/scripts/bootstrap_repo/copilot-sync-test.bats` | `tests/adapters/copilot-cli/copilot-cli-adapter-test.bats` | Foco no output, espelha estrutura |
| `tests/scripts/bootstrap_repo/opencode-link-test.bats` | `tests/adapters/opencode/opencode-adapter-test.bats` | Idem |
| `tests/copilot-int-test/` | `tests/integration/` | Rename |
| `tests/opencode-int-test/` | `tests/integration/` | Rename |

## 7. Migracao

### 7.1. Para usuarios OpenCode

1. `git pull` para obter nova estrutura
2. `./scripts/bootstrap_repo/configurar-repo.sh --yes`
3. Symlinks recriados apontando para novos paths
4. Nenhuma mudanca manual necessaria

### 7.2. Para usuarios Copilot (ex-VS Code)

1. `git pull` para obter nova estrutura
2. Remover artifacts VS Code antigos:
   ```
   rm -rf ~/.vscode-server/data/User/prompts/
   rm -f ~/.vscode-server/data/User/mcp.json
   ```
3. `./scripts/bootstrap_repo/configurar-repo.sh --yes`
4. Instalar Copilot CLI: `npm install -g @github/copilot`
5. `copilot --login`
6. Verificar: `copilot --help` e `/skills list`

### 7.3. Para usuarios novos

1. Clonar repo
2. `./scripts/bootstrap_repo/configurar-repo.sh --yes`
3. Pronto — ambas plataformas configuradas

## 8. Dependencias

| Dependencia | Versao minima | Usado por |
|---|---|---|
| OpenCode | ultima versao | Adapter OpenCode |
| GitHub Copilot CLI | >= 1.0 (suporta `.agent.md`) | Adapter Copilot CLI |
| Node.js | >= 18 (para `npx exa-mcp-server`) | MCP servers |
| Python 3 | >= 3.8 (para transforms no sync) | Adapter Copilot CLI |
| BATS-core | >= 1.10 | Testes |
| bash | >= 5.0 | Scripts |

## 9. Etapas de Execucao

### Fase 1: Fundacao — reestruturar diretorios

#### Task 1.1: Criar pasta adapters/

**Descricao:** criar a estrutura de pastas para adapters.

**Criterios de aceite:**
- [ ] `adapters/opencode/` existe
- [ ] `adapters/copilot-cli/` existe
- [ ] Ambos tem `README.md` com instrucoes de uso

**Verificacao:**
- [ ] `ls adapters/opencode/` e `ls adapters/copilot-cli/`

**Dependencias:** nenhuma
**Arquivos:** `adapters/opencode/README.md`, `adapters/copilot-cli/README.md`
**Escopo:** XS

---

#### Task 1.2: Mover scripts de bootstrap para adapters/

**Descricao:** mover scripts existentes para a nova
estrutura, renomeando conforme padrao `{plataforma}-adapter.{sh,ps1}`.

**Criterios de aceite:**
- [ ] `scripts/bootstrap_repo/opencode-link.sh` movido para `adapters/opencode/opencode-adapter.sh`
- [ ] `scripts/bootstrap_repo/wsl-copilot-sync.sh` movido para `adapters/copilot-cli/copilot-cli-adapter.sh`
- [ ] `scripts/bootstrap_repo/copilot-sync.ps1` movido para `adapters/copilot-cli/copilot-cli-adapter.ps1`
- [ ] Git history preservado (`git mv`)
- [ ] Scripts continuam executaveis (`chmod +x`)

**Verificacao:**
- [ ] `git status` mostra moves, nao delete+create
- [ ] `adapters/opencode/opencode-adapter.sh --help` funciona
- [ ] `adapters/copilot-cli/copilot-cli-adapter.sh --help` funciona
- [ ] `make test-opencode` continua passando (testes antigos ainda referenciam paths antigos — ok nesta fase)

**Dependencias:** Task 1.1
**Arquivos:** os 3 scripts movidos
**Escopo:** S

---

#### Task 1.3: Atualizar configurar-repo.sh para chamar adapters

**Descricao:** o orquestrador passa a invocar os
adapters nos novos paths.

**Criterios de aceite:**
- [ ] `configurar-repo.sh` chama `adapters/opencode/opencode-adapter.sh`
- [ ] `configurar-repo.sh` chama `adapters/copilot-cli/copilot-cli-adapter.sh`
- [ ] Variaveis de skip atualizadas: `OPENCODE_SKIP_OPENCODE_ADAPTER`, `OPENCODE_SKIP_COPILOT_ADAPTER`
- [ ] Variaveis antigas removidas: `OPENCODE_SKIP_LINKS`, `OPENCODE_SKIP_COPILOT_SYNC`
- [ ] README.md do bootstrap atualizado

**Verificacao:**
- [ ] `./scripts/bootstrap_repo/configurar-repo.sh --yes` executa sem erro
- [ ] `make test-opencode` passa (testes do bootstrap)

**Dependencias:** Task 1.2
**Arquivos:** `scripts/bootstrap_repo/configurar-repo.sh`, `scripts/bootstrap_repo/README.md`
**Escopo:** S

---

#### Task 1.4: Renomear diretorios de teste

**Descricao:** mover testes de integracao para `tests/integration/`.

**Criterios de aceite:**
- [ ] `tests/copilot-int-test/` movido para `tests/integration/`
- [ ] `tests/opencode-int-test/` movido para `tests/integration/`
- [ ] Git history preservado (`git mv`)
- [ ] Makefile atualizado (target `test-opencode` referencia novo path)

**Verificacao:**
- [ ] `make test-opencode` executa testes de `tests/integration/`
- [ ] Testes passam (se deps instaladas)

**Dependencias:** nenhuma
**Arquivos:** dirs de teste, `Makefile`
**Escopo:** S

---

### Checkpoint: Fase 1

- [ ] `make test-opencode` passa completo
- [ ] `configurar-repo.sh --yes` executa sem erro
- [ ] Nenhuma referencia quebrada a paths antigos
- [ ] Revisao com humano antes de prosseguir

---

### Fase 2: Adapter Copilot CLI

#### Task 2.1: Implementar convert_agent_frontmatter

**Descricao:** substituir `strip_agent_frontmatter` por
funcao que gera frontmatter Copilot CLI completo
conforme decisao 1.1 (tabela de mapeamento).

**Criterios de aceite:**
- [ ] `convert_agent_frontmatter` em Python (inline no bash)
- [ ] Converte `permission.edit: allow` → `tools` inclui `edit`
- [ ] Converte `permission.bash: allow` → `tools` inclui `execute`
- [ ] Converte `mode: subagent` → `user-invocable: false`
- [ ] Descarta `temperature`
- [ ] Mantem `description` inalterada
- [ ] Mesmo para PowerShell (copilot-cli-adapter.ps1)

**Verificacao:**
- [ ] Testar com `agents/eng-software.md` como input
- [ ] Output tem frontmatter valido YAML
- [ ] Output tem `tools: [...]` correto

**Dependencias:** Task 1.2
**Arquivos:** `adapters/copilot-cli/copilot-cli-adapter.sh`, `adapters/copilot-cli/copilot-cli-adapter.ps1`
**Escopo:** M

---

#### Task 2.2: Atualizar destinos para ~/.copilot/agents/

**Descricao:** mudar destino de agents de paths VS Code
para `~/.copilot/agents/`.

**Criterios de aceite:**
- [ ] `prompts_dir` / `$PromptsDir` aponta para `~/.copilot/agents`
- [ ] `mcp_json` removido (VS Code `mcp.json`)
- [ ] `windows_prompts_dir` removido
- [ ] `detect_windows_targets` removida
- [ ] `sync_mcp` removida

**Verificacao:**
- [ ] Rodar adapter com `$DestRoot` apontando para temp dir
- [ ] Verificar que agents vao para `$DestRoot/.copilot/agents/`
- [ ] Nenhum arquivo vai para paths VS Code

**Dependencias:** Task 2.1
**Arquivos:** `adapters/copilot-cli/copilot-cli-adapter.sh`, `adapters/copilot-cli/copilot-cli-adapter.ps1`
**Escopo:** M

---

#### Task 2.3: Implementar sync_commands_as_skills

**Descricao:** converter commands em skills com
description curta durante o sync.

**Criterios de aceite:**
- [ ] Funcao `sync_commands_as_skills` implementada
- [ ] `commands/index-codebase.md` → `skills/index-codebase/SKILL.md` com frontmatter
- [ ] `commands/bench-indexing.md` → `skills/bench-indexing/SKILL.md`
- [ ] `commands/sync-upstream-skills.md` → `skills/sync-upstream-skills/SKILL.md`
- [ ] Descriptions curtas e especificas (evitam ativacao inadvertida)

**Verificacao:**
- [ ] Rodar adapter com `$DestRoot` para temp dir
- [ ] Verificar que 3 skills geradas em `$DestRoot/.copilot/skills/`
- [ ] Cada SKILL.md tem `name` + `description` validos

**Dependencias:** Task 2.2
**Arquivos:** `adapters/copilot-cli/copilot-cli-adapter.sh`, `adapters/copilot-cli/copilot-cli-adapter.ps1`
**Escopo:** M

---

#### Task 2.4: Default-artifacts para ~/.copilot/agents/

**Descricao:** copiar `agents/default-artifacts/` para
`~/.copilot/agents/default-artifacts/`.

**Criterios de aceite:**
- [ ] `doc-readme.md` copiado para `$DestRoot/.copilot/agents/default-artifacts/`
- [ ] `harness-section.md` copiado para `$DestRoot/.copilot/agents/default-artifacts/`

**Verificacao:**
- [ ] Rodar adapter com `$DestRoot` para temp dir
- [ ] Verificar 2 arquivos em `$DestRoot/.copilot/agents/default-artifacts/`

**Dependencias:** Task 2.2
**Arquivos:** `adapters/copilot-cli/copilot-cli-adapter.sh`, `adapters/copilot-cli/copilot-cli-adapter.ps1`
**Escopo:** S

---

#### Task 2.5: Estender Adapt-SkillForCopilot (frontmatter)

**Descricao:** adicionar frontmatter YAML a skills que
nao tem (decisao 1.5).

**Criterios de aceite:**
- [ ] Funcao detecta SKILL.md sem frontmatter
- [ ] Gera `name` do nome do diretorio
- [ ] Gera `description` do primeiro paragrafo
- [ ] Valida name (lowercase, hyphens, max 64 chars)

**Verificacao:**
- [ ] Testar com `skills/browser-testing/SKILL.md` (sem frontmatter)
- [ ] Output tem frontmatter valido

**Dependencias:** Task 2.2
**Arquivos:** `adapters/copilot-cli/copilot-cli-adapter.sh`, `adapters/copilot-cli/copilot-cli-adapter.ps1`
**Escopo:** M

---

#### Task 2.6: Adicionar frontmatter ao browser-testing

**Descricao:** corrigir no repo fonte (decisao 1.5).

**Criterios de aceite:**
- [ ] `skills/browser-testing/SKILL.md` tem frontmatter com `name: browser-testing` e `description`
- [ ] `name` bate com nome do diretorio

**Verificacao:**
- [ ] `head -5 skills/browser-testing/SKILL.md` mostra `---` + frontmatter

**Dependencias:** nenhuma
**Arquivos:** `skills/browser-testing/SKILL.md`
**Escopo:** XS

---

### Checkpoint: Fase 2

- [ ] `make test-opencode` passa completo
- [ ] Adapter Copilot CLI gera output correto em temp dir
- [ ] Todos os agents tem `.agent.md` com frontmatter Copilot CLI
- [ ] 3 commands convertidos para skills
- [ ] Default-artifacts copiados
- [ ] Skills sem frontmatter recebem frontmatter
- [ ] Revisao com humano antes de prosseguir

---

### Fase 3: Adapter OpenCode

#### Task 3.1: Refatorar opencode-adapter.sh

**Descricao:** adaptar script como adapter formal,
remover referencias a VS Code.

**Criterios de aceite:**
- [ ] Script usa nome `opencode-adapter.sh` internamente (help, logs)
- [ ] Sem referencias a VS Code, Copilot Chat, ou paths antigos
- [ ] Mantem funcionalidade de symlinks existente

**Verificacao:**
- [ ] `adapters/opencode/opencode-adapter.sh --help` exibe help atualizado
- [ ] Rodar adapter cria symlinks corretos
- [ ] `make test-opencode` passa

**Dependencias:** Task 1.2
**Arquivos:** `adapters/opencode/opencode-adapter.sh`
**Escopo:** S

---

### Checkpoint: Fase 3

- [ ] `make test-opencode` passa completo
- [ ] Ambos adapters funcionais
- [ ] Revisao com humano antes de prosseguir

---

### Fase 4: Prompts e documentacao

#### Task 4.1: Atualizar agents/devflow.md

**Descricao:** remover referencias a VS Code, adicionar
politica de sessao Copilot CLI.

**Criterios de aceite:**
- [ ] Linha 154: "VS Code" → "Copilot CLI: use `/model` ou defina na sessao"
- [ ] Nova secao sobre politica de sessao por fase (decisao 1.3)
- [ ] Session ID estruturado documentado
- [ ] Sem outras referencias a "VS Code" ou "runSubagent"

**Verificacao:**
- [ ] `grep -i "vs code\|runsubagent" agents/devflow.md` retorna vazio
- [ ] `make test-opencode` passa (testes de agente validam conteudo)

**Dependencias:** Task 2.1 (decisao de frontmatter informa politica)
**Arquivos:** `agents/devflow.md`
**Escopo:** S

---

#### Task 4.2: Atualizar docs/workflow-agentes-dev.md

**Descricao:** remover VS Code, atualizar Copilot CLI,
alinhar com plano mediador.

**Criterios de aceite:**
- [ ] Linha 221: "VS Code" → "Copilot CLI"
- [ ] Linha 851-862: tabela de interacao atualizada (VS Code removido)
- [ ] Premissa 7: aplicacao por plataforma atualizada
- [ ] Nota sobre mediador adicionada (deferida do plano devflow-mediador)

**Verificacao:**
- [ ] `grep -i "vs code" docs/workflow-agentes-dev.md` retorna vazio
- [ ] `make test-opencode` passa

**Dependencias:** Task 4.1
**Arquivos:** `docs/workflow-agentes-dev.md`
**Escopo:** M

---

#### Task 4.3: Atualizar README.md

**Descricao:** remover secoes VS Code, documentar
estrutura adapters/.

**Criterios de aceite:**
- [ ] Secao "VS Code Server (WSL)" removida ou renomeada
- [ ] Secao "VS Code Windows" removida
- [ ] Nova secao documentando `adapters/`
- [ ] Tabela de artefatos sincronizados atualizada
- [ ] Instrucoes de bootstrap atualizadas

**Verificacao:**
- [ ] `grep -i "vs code" README.md` retorna vazio (exceto `.vscode/settings.json` se existir)
- [ ] README renderiza corretamente

**Dependencias:** Tasks 1.1-1.4 (estrutura final definida)
**Arquivos:** `README.md`
**Escopo:** M

---

### Checkpoint: Fase 4

- [ ] `grep -ri "vs code" agents/ docs/ README.md` retorna vazio (exceto paths IDE)
- [ ] `make test-opencode` passa completo
- [ ] Revisao com humano antes de prosseguir

---

### Fase 5: Testes de adapter

#### Task 5.1: Criar tests/adapters/opencode/opencode-adapter-test.bats

**Descricao:** testes do adapter OpenCode.

**Criterios de aceite:**
- [ ] Testa que symlinks sao criados nos destinos corretos
- [ ] Testa que variaveis de skip funcionam
- [ ] Testa que agents, skills, commands sao linkados
- [ ] Usa temp dir para isolamento

**Verificacao:**
- [ ] `bats tests/adapters/opencode/opencode-adapter-test.bats` passa

**Dependencias:** Task 3.1
**Arquivos:** `tests/adapters/opencode/opencode-adapter-test.bats`
**Escopo:** M

---

#### Task 5.2: Criar tests/adapters/copilot-cli/copilot-cli-adapter-test.bats

**Descricao:** testes do adapter Copilot CLI.

**Criterios de aceite:**
- [ ] Testa conversao de frontmatter (decisao 1.1)
- [ ] Testa que agents geram `.agent.md` com `tools`
- [ ] Testa que commands viram skills (decisao 1.4)
- [ ] Testa que default-artifacts sao copiados
- [ ] Testa que skills sem frontmatter recebem frontmatter (decisao 1.5)
- [ ] Testa que `$DestRoot` funciona para isolamento
- [ ] Testa que variaveis de skip funcionam

**Verificacao:**
- [ ] `bats tests/adapters/copilot-cli/copilot-cli-adapter-test.bats` passa

**Dependencias:** Tasks 2.1-2.5
**Arquivos:** `tests/adapters/copilot-cli/copilot-cli-adapter-test.bats`
**Escopo:** L (muitos cenarios)

---

#### Task 5.3: Migrar testes de bootstrap existentes

**Descricao:** mover e adaptar testes antigos que
testavam os scripts nos paths antigos.

**Criterios de aceite:**
- [ ] Testes de `tests/scripts/bootstrap_repo/copilot-sync-test.bats` migrados ou substituidos
- [ ] Testes de `tests/scripts/bootstrap_repo/opencode-link-test.bats` migrados ou substituidos
- [ ] Paths antigos nao existem mais em `tests/scripts/bootstrap_repo/` (se todos migrados)

**Verificacao:**
- [ ] `make test-opencode` passa completo
- [ ] Sem testes duplicados (antigo + novo)

**Dependencias:** Tasks 5.1, 5.2
**Arquivos:** `tests/scripts/bootstrap_repo/*.bats`
**Escopo:** M

---

### Checkpoint: Fase 5

- [ ] `make test-opencode` passa completo (todos os testes)
- [ ] Testes de adapter cobrem todas as decisoes (1.1, 1.4, 1.5)
- [ ] Revisao com humano antes de prosseguir

---

### Fase 6: Verificacao final

#### Task 6.1: Validacao OpenCode

**Descricao:** verificar que OpenCode funciona com a
nova estrutura.

**Criterios de aceite:**
- [ ] `adapters/opencode/opencode-adapter.sh --yes` executa sem erro
- [ ] Symlinks criados em `~/.config/opencode/`
- [ ] `opencode` carrega agents (verificar `/agents` ou equivalente)
- [ ] `opencode` carrega skills (verificar `/skills` ou equivalente)
- [ ] Commands funcionam como slash commands

**Verificacao:**
- [ ] Abrir `opencode` em um projeto qualquer
- [ ] Verificar que agents aparecem
- [ ] Verificar que skills aparecem
- [ ] Executar um command e verificar que funciona

**Dependencias:** Tasks 3.1, 4.1-4.3
**Arquivos:** nenhum (verificacao manual)
**Escopo:** S

---

#### Task 6.2: Validacao Copilot CLI

**Descricao:** verificar que Copilot CLI funciona com
a nova estrutura.

**Criterios de aceite:**
- [ ] `adapters/copilot-cli/copilot-cli-adapter.sh --yes` executa sem erro
- [ ] `copilot --help` funciona
- [ ] `/skills list` mostra todas as skills (incluindo as 3 convertidas de commands)
- [ ] Agents visiveis em `.github/agents/` ou `~/.copilot/agents/`
- [ ] MCP servers funcionam (`mcp --list`)

**Verificacao:**
- [ ] `copilot --help` retorna exit 0
- [ ] `copilot` em modo interativo: `/skills list` mostra skills
- [ ] `copilot` em modo interativo: agent custom visivel

**Dependencias:** Tasks 2.1-2.6
**Arquivos:** nenhum (verificacao manual)
**Escopo:** S

---

#### Task 6.3: Validacao cross-platform

**Descricao:** verificar que mesmo repo funciona em
ambas plataformas sem conflito.

**Criterios de aceite:**
- [ ] Ambos adapters rodam sem conflito
- [ ] Mudanca em fonte canonica (ex: editar um agente) reflete em ambas plataformas apos re-sync
- [ ] Sem paths hardcoded especificos de plataforma na fonte canonica

**Verificacao:**
- [ ] Editar `agents/eng-software.md` (adicionar comentario temporario)
- [ ] Rodar ambos adapters
- [ ] Verificar que OpenCode ve a mudanca (symlink)
- [ ] Verificar que Copilot CLI ve a mudanca (re-sync)
- [ ] Reverter edicao temporaria

**Dependencias:** Tasks 6.1, 6.2
**Arquivos:** nenhum (verificacao manual)
**Escopo:** S

---

### Checkpoint final

- [ ] `make test-opencode` passa completo
- [ ] OpenCode funciona (Task 6.1)
- [ ] Copilot CLI funciona (Task 6.2)
- [ ] Cross-platform funciona (Task 6.3)
- [ ] Nenhuma referencia a "VS Code" em agents, docs, README
- [ ] `AGENTS.md` atualizado com nova estrutura
- [ ] Revisao final com humano
