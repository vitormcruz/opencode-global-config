# Plano de Testes Automatizados — opencode-config

> Status: PROPOSTA v3 — aguardando revisão e aprovação.
> Data: 2026-04-06
> Atualizado: 2026-04-07 (v3: AGENTS.md local, 5 symlinks, regra de
> testes, upstream de skills)

---

## 1. Resumo do Problema

Este repositório é a fonte de verdade das configurações globais do
OpenCode. O bootstrap (`scripts/bootstrap_repo/opencode-link`) cria symlinks em
`~/.config/opencode`, edita `~/.bashrc` e instala dependências. Hoje
**não existe nenhum teste automatizado** que valide se esse processo
produz o estado esperado. Qualquer alteração pode quebrar o setup
silenciosamente.

---

## 2. Arquitetura de Duas Camadas

### Camada 1 — Local (sandbox `/tmp`)

- `HOME` redirecionado para diretório temporário
- Sem Docker, sem OpenCode, sem LLM
- Testes rápidos de scripts shell via BATS
- Cobre: bootstrap, estrutura estática, wrappers, scripts auxiliares

### Camada 2 — Docker (container Ubuntu + OpenCode)

- Container persistente com OpenCode instalado
- Repo copiado + `scripts/bootstrap_repo/opencode-link --yes` executado dentro do container
- `opencode serve` rodando dentro do container
- Testes fazem chamadas HTTP à API
- Cobre: listagem de agentes/MCPs, prompts, ativação de skills,
  slash commands

> **Nota:** `AGENTS.md` é arquivo de instruções **deste projeto**,
> não uma configuração global do OpenCode. O bootstrap linka apenas
> `agents/`, `commands/`, `opencode.json`, `skills/` e `scripts/`.

---

## 3. O Que Precisa Ser Testado

### 3.1 Bootstrap (`scripts/bootstrap_repo/opencode-link`)

| Aspecto | Validação |
|---------|-----------|
| Criação de `~/.config/opencode/` | Diretório existe após execução |
| 5 symlinks | Cada link aponta para o caminho correto no repo |
| `AGENTS.md` não linkado | `~/.config/opencode/AGENTS.md` **não** existe |
| Idempotência | Rodar 2× não duplica nada, links continuam OK |
| Backup | Se destino já existe, é movido para backup |
| `.bashrc` | Linha `OPENCODE_ENABLE_EXA=1` presente, sem duplicata |
| `--yes` | Executa sem TTY |
| `--help` | Exibe ajuda, exit 0 |
| Opção inválida | Exit 2 |

### 3.2 Verificação de dependências (`scripts/bootstrap_repo/opencode-install-deps`)

| Aspecto | Validação |
|---------|-----------|
| Detecção de OS | Retorna `wsl`, `linux` ou `macos` |
| `--help` | Exibe ajuda, exit 0 |
| `--quiet` | Suprime saída de progresso |
| Dependência presente | Exibe `OK` |
| Dependência ausente | Exibe `MISSING` + hint |

### 3.3 Wrappers de skills

| Script | Validações |
|--------|------------|
| `opencode-doc-extract` | JSON `ok:true` com PDF fixture; `ok:false`
sem `source`; `ok:false` sem `docling` no PATH |
| `opencode-md-export` | JSON `ok:true` com MD fixture → DOCX;
`ok:false` sem `source`; não sobrescreve sem `--overwrite`;
`ok:false` sem `pandoc` |
| `opencode-svgtoimage` | JSON com `imagePath` → PNG existe; erro
sem conversor |

### 3.4 Scripts auxiliares

| Script | Validações |
|--------|------------|
| `skills/list-updatable` | Lista coerente com skills que têm
`UPSTREAM.md` |
| `skills/update-upstream-skill` | `--help` funciona; skill
inexistente → erro |
| `prompt-improver/sync` | `--help` funciona; `--check-only` não
altera arquivos |

### 3.5 Crawl4AI (`install-crawl4ai-mcp.sh`)

| Aspecto | Validação |
|---------|-----------|
| Responsabilidade única | Só altera `~/.bashrc`, sem criar ou
sobrescrever arquivos em `~/.config/opencode/` (requer refatoração) |
| Sem `AGENTS.md` global | Não cria `~/.config/opencode/AGENTS.md`
nem referencia `instructions` apontando para ele |
| Docker check | Aborta se Docker não disponível |
| `.bashrc` idempotente | Bloco adicionado corretamente; sem duplicata
ao rodar 2× |

### 3.6 Estrutura estática do repo

| Aspecto | Validação |
|---------|-----------|
| Arquivos obrigatórios do repo | `AGENTS.md`, `opencode.json`,
`README.md` existem |
| Itens linkados globalmente | Apenas `agents/`, `commands/`,
`opencode.json`, `skills/`, `scripts/` |
| Skills | Cada dir em `skills/` contém `SKILL.md` |
| Agentes | Cada `.md` em `agents/` tem frontmatter válido |
| `opencode.json` | JSON válido |
| Permissões | Scripts em `scripts/` são executáveis |

### 3.7 Testes comportamentais do OpenCode (Camada 2)

| Aspecto | Validação |
|---------|-----------|
| `GET /agent` | Retorna os 4 agentes do repo |
| `GET /mcp` | Crawl4AI listado |
| `GET /config/providers` | Provider configurado aparece |
| `POST /session/:id/message` | Prompt simples retorna resposta |
| Ativação de skill | Prompt que aciona skill → resposta coerente |
| Slash command | `/sync-upstream-skills` executável |
| Seleção de agente | `POST` com `agent` específico funciona |

---

## 4. Stack

**BATS-core** com libs oficiais:

- `bats-core` — framework de testes para Bash
- `bats-assert` — asserções de output (`assert_success`,
  `assert_output`, etc.)
- `bats-file` — asserções de filesystem (`assert_symlink_to`,
  `assert_file_exist`, `assert_dir_exist`, etc.)

Instalação via git submodules em `tests/bats-libs/`.

---

## 5. Configuração do Container Docker

### 5.1 Fluxo de criação (primeira execução ou container excluído)

```
1. Script pergunta:
   "Usar provider configurado ou OpenCode Zen (modelos grátis)?"

   Opção A — Provider configurado:
     → Pergunta qual provider (ex: anthropic, openai, google)
     → Pergunta nome da env var do HOST com a API key
       (ex: ANTHROPIC_API_KEY)
     → Pergunta qual modelo (ex: anthropic/claude-sonnet-4-20250514)

   Opção B — OpenCode Zen:
     → Usa env var OPENCODE_API_KEY do HOST
     → Pergunta qual modelo do Zen

2. Salva em tests/.test-env (gitignored):
     OPENCODE_TEST_MODE=provider|zen
     OPENCODE_TEST_PROVIDER=anthropic
     OPENCODE_TEST_MODEL=anthropic/claude-sonnet-4-20250514
     OPENCODE_TEST_API_KEY_VAR=ANTHROPIC_API_KEY

   IMPORTANTE: a key real NUNCA é salva — só o nome da env var do host.

3. Container é criado e mantido persistente.
```

### 5.2 Execuções subsequentes

- Container existe → reutiliza (sem perguntas)
- Container excluído → repete o fluxo de criação

### 5.3 Mapeamento da API key

Na hora do `docker run`, o script lê `OPENCODE_TEST_API_KEY_VAR` do
`.test-env`, busca o valor real no host e passa via `docker run -e`.
A key nunca fica em arquivo — só transita via variável de ambiente.

### 5.4 Dockerfile

```dockerfile
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y curl git jq
RUN curl -fsSL https://opencode.ai/install | bash
COPY . /opt/opencode-config
WORKDIR /opt/opencode-config
RUN bash ./scripts/bootstrap_repo/opencode-link --yes
EXPOSE 4096
```

---

## 6. Estrutura de Diretórios

```
tests/
├── bats-libs/                # git submodules
│   ├── bats-core/
│   ├── bats-assert/
│   └── bats-file/
├── fixtures/
│   ├── sample.pdf
│   ├── sample.md
│   └── sample.svg
├── helpers/
│   └── test_helper.bash      # setup/teardown compartilhado
├── scripts/
│   └── bootstrap_repo/
│       ├── opencode-link_test.bats
│       └── opencode-install-deps_test.bats
├── wrappers/
│   ├── doc-extract.bats
│   ├── md-export.bats
│   └── svgtoimage.bats
├── skills/
│   ├── list-updatable.bats
│   └── update-upstream-skill.bats
├── crawl4ai/
│   └── install-crawl4ai-mcp.bats
├── structure/
│   └── repo-structure.bats
├── behavioral/               # Camada 2 — Docker
│   ├── agents.bats
│   ├── mcp.bats
│   ├── prompts.bats
│   ├── skills-activation.bats
│   └── commands.bats
├── smoke.bats
├── Dockerfile
├── setup-container.sh        # criação interativa do container
└── .test-env                 # gitignored — nunca commitar
```

---

## 7. Plano de Implementação em Etapas

### Etapa 1 — Infraestrutura BATS

**O quê:** Instalar BATS e criar estrutura base.

- Git submodules: bats-core, bats-assert, bats-file em
  `tests/bats-libs/`
- `tests/helpers/test_helper.bash` com funções de setup/teardown e
  variáveis de caminho comuns
- `Makefile` na raiz com targets:
  - `make test` — todos os testes da Camada 1
  - `make test-unit` — só estrutura estática
  - `make test-integration` — só wrappers (precisa de deps externas)
  - `make test-smoke` — só smoke test
  - `make test-behavioral` — Camada 2 (Docker)
- 1 teste trivial para validar que a infra funciona
- Atualizar `.gitignore` com `tests/.test-env`

**Entregável:** `bats tests/` funciona e exibe 1 teste passando.

---

### Etapa 2 — Testes de Estrutura Estática

**O quê:** Validar que o repo tem a estrutura esperada (sem deps).

- `tests/structure/repo-structure.bats`:
  - Arquivos obrigatórios existem
  - Cada skill tem `SKILL.md`
  - `opencode.json` é JSON válido
  - Agentes têm frontmatter válido
  - Scripts são executáveis (`-x`)

**Entregável:** ~15-20 testes.

---

### Etapa 3 — Testes do Bootstrap (`scripts/bootstrap_repo/opencode-link`)

**O quê:** Testar o fluxo principal do repo.

- `tests/scripts/bootstrap_repo/opencode-link_test.bats`:
  - Execução com `--yes` em sandbox
  - Validação dos 5 symlinks (`assert_symlink_to`)
  - Validar que `~/.config/opencode/AGENTS.md` **não** é criado
  - Idempotência (rodar 2×)
  - Backup de configs pré-existentes
  - `.bashrc` contém `OPENCODE_ENABLE_EXA=1`
  - Sem duplicatas no `.bashrc` após 2ª execução
  - `--help` retorna 0
  - Opção inválida retorna 2

**Entregável:** ~10-15 testes.

---

### Etapa 4 — Testes do `scripts/bootstrap_repo/opencode-install-deps`

**O quê:** Testar detecção de deps e formatação de saída.

- `tests/scripts/bootstrap_repo/opencode-install-deps_test.bats`:
  - `--help` retorna 0
  - `--quiet` suprime saída
  - Detecção de OS funciona
  - Com dependência presente → exibe `OK`
  - Com dependência ausente → exibe `MISSING` + hint

**Entregável:** ~8-10 testes.

---

### Etapa 5 — Refatoração do `install-crawl4ai-mcp.sh` + Testes

**O quê:** Restringir o script à sua única responsabilidade real.

**Problema:** O script hoje cria arquivos diretamente em
`~/.config/opencode/` (`opencode.json`, `AGENTS.md`,
`scripts/crawl4ai/`), conflitando com os symlinks do
`scripts/bootstrap_repo/opencode-link`.
O `opencode.json` deste repo já inclui a config do MCP do Crawl4AI.

**Refatoração:** O script deve ficar responsável apenas por:

1. Verificar que Docker está instalado e em execução
2. Fazer pull da imagem `unclecode/crawl4ai:latest`
3. Fazer build da imagem `crawl4ai-sanitized:latest`
4. Garantir o bloco de auto-start no `~/.bashrc` (idempotente)
5. Iniciar o container pela primeira vez

Tudo que cria arquivos em `~/.config/opencode/` deve ser removido.

**Testes** (`tests/crawl4ai/install-crawl4ai-mcp.bats`):

- Docker indisponível → aborta com erro
- Não cria nem modifica arquivos em `~/.config/opencode/`
- Adiciona bloco com markers no `.bashrc` do sandbox
- Sem duplicata ao rodar 2×

**Entregável:** Script refatorado + ~5-8 testes.

---

### Etapa 6 — Testes dos Wrappers de Skills

**O quê:** Validar execução real dos wrappers com ferramentas reais.

- `tests/wrappers/doc-extract.bats`:
  - Entrada válida (PDF fixture) → JSON `ok:true`, artifact existe
  - Sem campo `source` → JSON `ok:false`
  - Formato inválido → JSON `ok:false`
  - Sem `docling` no PATH → JSON `ok:false` com hint

- `tests/wrappers/md-export.bats`:
  - MD fixture → DOCX gerado, JSON `ok:true`
  - Sem `source` → `ok:false`
  - Arquivo já existe sem `--overwrite` → `ok:false`
  - Sem `pandoc` → `ok:false` com hint

- `tests/wrappers/svgtoimage.bats`:
  - SVG fixture via stdin → JSON com `imagePath`, PNG existe
  - Sem conversor → exit 1

**Entregável:** ~20-25 testes de integração.

---

### Etapa 7 — Testes dos Scripts Auxiliares de Skills

**O quê:** Validar scripts de gerenciamento de skills.

- `tests/skills/list-updatable.bats`:
  - Saída coerente com skills que têm `UPSTREAM.md`
  - Ordem alfabética

- `tests/skills/update-upstream-skill.bats`:
  - `--help` funciona
  - Skill inexistente → erro

**Entregável:** ~5-8 testes.

---

### Etapa 8 — Atualização do `AGENTS.md` do projeto

**O quê:** Tornar o `AGENTS.md` adequado ao seu papel de instrução
deste projeto, removendo o que não pertence a ele e adicionando
regras permanentes.

**Mudanças:**

1. Remover a seção `## Imagens e diagramas` — esse comportamento
   pertence à skill `svg-to-image` e deve viver em
   `skills/svg-to-image/SKILL.md`
2. Adicionar regra de testes obrigatórios:
   - Toda evolução funcional do repo deve criar ou atualizar testes
   - Válido para: novos scripts, skills, comandos, agentes e
     mudanças no bootstrap
3. Adicionar padrão de upstream para skills externas:
   - Skills baseadas em repositórios externos devem seguir o
     esquema já existente no repo (`UPSTREAM.md` + script de sync)
   - Ao criar uma skill desse tipo, registrar origem e estruturar
     para permitir atualização futura

**Entregável:** `AGENTS.md` atualizado.

---

### Etapa 9 — Smoke Test E2E

**O quê:** Teste de ponta a ponta na Camada 1.

- `tests/smoke.bats`:
  - Executa `opencode-link --yes` em sandbox
  - Valida os 5 symlinks
  - Valida que `~/.config/opencode/AGENTS.md` não existe
  - Valida `.bashrc`
  - Valida que `opencode.json` no destino é legível e válido
  - Valida que skills são acessíveis via symlink

**Entregável:** ~5-10 testes.

---

### Etapa 10 — Dockerfile + Setup Interativo do Container

**O quê:** Infraestrutura da Camada 2.

- `tests/Dockerfile`:
  - Base Ubuntu 24.04
  - OpenCode instalado via `curl | bash`
  - Repo copiado + `opencode-link --yes` executado
  - Porta 4096 exposta

- `tests/setup-container.sh`:
  - Verifica se container existe → reutiliza
  - Se não existe → pergunta interativamente:
    - Provider configurado ou Zen?
    - Qual provider/modelo?
    - Nome da env var do host com a API key?
  - Salva configuração em `tests/.test-env` (gitignored)
  - Configura provider dentro do container via API do OpenCode
  - Sobe container persistente

- `tests/.test-env` adicionado ao `.gitignore`

**Entregável:** `make test-behavioral` sobe container e conecta.

---

### Etapa 11 — Testes Comportamentais do OpenCode

**O quê:** Validar comportamento do OpenCode via API HTTP.

- `tests/behavioral/agents.bats`:
  - `GET /agent` retorna os 4 agentes do repo
  - Cada agente tem os campos esperados

- `tests/behavioral/mcp.bats`:
  - `GET /mcp` lista crawl4ai
  - Status do MCP é `connected`

- `tests/behavioral/prompts.bats`:
  - Prompt simples retorna resposta coerente
  - Resposta em PT-BR quando solicitado
  - Seleção de agente específico funciona

- `tests/behavioral/skills-activation.bats`:
  - Prompt que aciona skill doc-extract → resposta com uso da skill
  - Prompt que aciona skill md-export → resposta com uso da skill

- `tests/behavioral/commands.bats`:
  - Slash command `/sync-upstream-skills` é reconhecido

**Entregável:** ~15-20 testes comportamentais.

---

## 8. Resumo das Etapas

| Etapa | Camada | ~Testes |
|-------|--------|---------|
| 1. Infraestrutura | — | 1 |
| 2. Estrutura estática | Local | 15–20 |
| 3. Bootstrap | Local | 10–15 |
| 4. Install-deps | Local | 8–10 |
| 5. Crawl4AI refatoração | Local | 5–8 |
| 6. Wrappers | Local | 20–25 |
| 7. Auxiliares | Local | 5–8 |
| 8. Atualização AGENTS.md | — | — |
| 9. Smoke | Local | 5–10 |
| 10. Docker setup | Docker | — |
| 11. Comportamentais | Docker | 15–20 |
| **Total** | | **~85–117** |

---

## 9. Riscos e Trade-offs

| Item | Risco | Mitigação |
|------|-------|-----------|
| Deps externas (wrappers) | Testes falham sem pandoc/docling/resvg |
Separar em `make test-integration` |
| Docker nos comportamentais | Precisa de Docker instalado | Skip se
Docker indisponível |
| Fixtures PDF | Binário no repo | PDF mínimo ~5KB |
| Provider nos comportamentais | Precisa de API key | Setup
interativo; skip se sem provider |
| Custo de LLM | Testes comportamentais gastam tokens | Prompts
mínimos, poucos testes |

---

## 10. Decisões Fechadas

| # | Decisão | Resolução |
|---|---------|-----------|
| 1 | `install-crawl4ai-mcp.sh` | Só altera `~/.bashrc`; não cria
`AGENTS.md` global |
| 2 | Fixture PDF | Commitar PDF mínimo em `tests/fixtures/` |
| 3 | Coverage (`kcov`) | Fora do escopo |
| 4 | Framework | BATS-core + bats-assert + bats-file |
| 5 | Isolamento | Duas camadas (local + Docker) |
| 6 | Nível de testes comportamentais | Máximo |
| 7 | API para testes comportamentais | `opencode serve` (HTTP) |
| 8 | Provider no container | Setup interativo na 1ª execução; env var
do host mapeada; `.test-env` gitignored |
| 9 | CI (GitHub Actions) | Fora do escopo |
| 10 | `AGENTS.md` | Arquivo do projeto; não linkado globalmente |
| 11 | Seção `Imagens e diagramas` | Removida do `AGENTS.md`; pertence
à skill `svg-to-image` |
| 12 | Novas skills externas | Devem seguir padrão de upstream
(`UPSTREAM.md` + script de sync) |

---

## Apêndice A: Exemplo — Teste Local (Camada 1)

```bash
#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/opencode-link_test.bats

load "../helpers/test_helper"

setup()    { common_setup; }
teardown() { common_teardown; }

@test "opencode-link --yes cria diretório ~/.config/opencode" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
  assert_dir_exist "$TEST_CONFIG_DIR"
}

@test "opencode-link --yes cria symlink para agents/" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
  assert_symlink_to "$TEST_CONFIG_DIR/agents" \
    "$REPO_ROOT/agents"
}

@test "opencode-link não cria symlink para AGENTS.md" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
  assert_not_exist "$TEST_CONFIG_DIR/AGENTS.md"
}

@test "opencode-link é idempotente" {
  bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
}

@test "opencode-link adiciona OPENCODE_ENABLE_EXA=1 ao .bashrc" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
  run grep "OPENCODE_ENABLE_EXA=1" "$TEST_BASHRC"
  assert_success
}
```

## Apêndice B: Exemplo — Teste Comportamental (Camada 2)

```bash
#!/usr/bin/env bats
# tests/behavioral/agents.bats

load "../helpers/test_helper"

setup_file() { start_opencode_serve; }
teardown_file() { stop_opencode_serve; }

@test "OpenCode carrega os 4 agentes do repo" {
  run curl -s "http://localhost:4096/agent"
  assert_success
  assert_output --partial "analista-bd"
  assert_output --partial "revisor-historia"
  assert_output --partial "analista"
  assert_output --partial "aws-analista"
}

@test "OpenCode responde a prompt simples" {
  SESSION=$(curl -s -X POST "http://localhost:4096/session" \
    | jq -r '.id')
  run curl -s -X POST \
    "http://localhost:4096/session/$SESSION/message" \
    -H "Content-Type: application/json" \
    -d '{"parts":[{"type":"text","text":"Responda apenas: ok"}]}'
  assert_success
  assert_output --partial "ok"
}
```
