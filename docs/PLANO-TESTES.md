# Plano de Testes Automatizados — opencode-config

> Status: PROPOSTA — aguardando revisão e aprovação.
> Data: 2026-04-06
> Atualizado: 2026-04-06 (decisões 1, 2 e 3 fechadas)

---

## 1. Resumo do Problema

Este repositório é a fonte de verdade das configurações globais do OpenCode. O bootstrap
(`scripts/opencode-link`) cria symlinks em `~/.config/opencode`, edita `~/.bashrc` e
instala dependências. Hoje **não existe nenhum teste automatizado** que valide se esse
processo produz o estado esperado. Qualquer alteração pode quebrar o setup
silenciosamente.

---

## 2. O Que Precisa Ser Testado

### 2.1 Bootstrap (`opencode-link`)

| Aspecto | Validação |
|---------|-----------|
| Criação de `~/.config/opencode/` | Diretório existe após execução |
| 6 symlinks | Cada link aponta para o caminho correto no repo |
| Idempotência | Rodar 2× não duplica nada, links continuam OK |
| Backup | Se destino já existe, é movido para backup |
| `.bashrc` | Linha `OPENCODE_ENABLE_EXA=1` presente, sem duplicata |
| `--yes` | Executa sem TTY |
| `--help` | Exibe ajuda, exit 0 |
| Opção inválida | Exit 2 |

### 2.2 Verificação de dependências (`opencode-install-deps`)

| Aspecto | Validação |
|---------|-----------|
| Detecção de OS | Retorna `wsl`, `linux` ou `macos` |
| `--help` | Exibe ajuda, exit 0 |
| `--quiet` | Suprime saída de progresso |
| Dependência presente | Exibe `OK` |
| Dependência ausente | Exibe `MISSING` + hint |

### 2.3 Wrappers de skills

| Script | Validações |
|--------|------------|
| `opencode-doc-extract` | JSON válido na stdout; campo `ok:true` com PDF de teste; `ok:false` sem `source`; `ok:false` sem `docling` no PATH |
| `opencode-md-export` | JSON válido; `ok:true` com MD de teste → DOCX; `ok:false` sem `source`; `ok:false` sem `pandoc`; não sobrescreve sem `--overwrite` |
| `opencode-svgtoimage` | JSON válido; `imagePath` aponta para PNG existente; erro sem conversor |

### 2.4 Scripts auxiliares

| Script | Validações |
|--------|------------|
| `skills/list-updatable` | Retorna lista coerente com skills que têm `UPSTREAM.md` |
| `skills/update-upstream-skill` | `--help` funciona; skill inexistente → erro |
| `prompt-improver/sync` | `--help` funciona; `--check-only` não altera arquivos |

### 2.5 Crawl4AI (`install-crawl4ai-mcp.sh`)

| Aspecto | Validação |
|---------|-----------|
| Responsabilidade única | Só altera `~/.bashrc`, sem criar/sobrescrever nenhum arquivo em `~/.config/opencode/` (requer refatoração — ver etapa 5) |
| Docker check | Aborta se Docker não disponível |
| `.bashrc` idempotente | Bloco Crawl4AI adicionado corretamente; sem duplicata ao rodar 2× |

### 2.6 Estrutura estática do repo

| Aspecto | Validação |
|---------|-----------|
| Arquivos obrigatórios | `AGENTS.md`, `opencode.json`, `README.md` existem |
| Skills | Cada dir em `skills/` contém `SKILL.md` |
| Agentes | Cada `.md` em `agents/` tem frontmatter válido |
| `opencode.json` | JSON válido, schema presente |
| Permissões | Scripts em `scripts/` são executáveis |

---

## 3. Stack Recomendada

### 3.1 Opções avaliadas

| Ferramenta | Prós | Contras |
|------------|------|---------|
| **BATS-core** | Padrão para shell scripts; libs `bats-assert` e `bats-file` para filesystem; TAP output; 6k+ stars; ativo | Só Bash |
| **ShellSpec** | BDD, multi-shell, coverage nativo | Menor comunidade, mais verboso |
| **shUnit2** | Simples, xUnit-style | Sem libs de filesystem, menos ativo |
| **pytest + subprocess** | Flexível, Python | Overhead de setup, mistura de linguagens |

### 3.2 Recomendação

**BATS-core** com as libs oficiais:

- `bats-core` — framework
- `bats-assert` — asserções (`assert_success`, `assert_output`, etc.)
- `bats-file` — asserções de filesystem (`assert_symlink_to`,
  `assert_file_exist`, `assert_dir_exist`, etc.)

Justificativa: o repo é 100% Bash; BATS é o padrão da indústria; `bats-file` tem
exatamente as asserções de symlink necessárias; integração trivial com GitHub Actions.

---

## 4. Isolamento do Ambiente de Teste

Estratégia: **sandbox em `/tmp`** com `$HOME` redirecionado.

```bash
# Em setup() de cada arquivo .bats:
setup() {
  TEST_HOME="$(mktemp -d)"
  TEST_CONFIG_DIR="$TEST_HOME/.config/opencode"
  TEST_BASHRC="$TEST_HOME/.bashrc"
  touch "$TEST_BASHRC"
  export HOME="$TEST_HOME"
}

teardown() {
  rm -rf "$TEST_HOME"
}
```

Isso garante que:

- Nenhum teste toca o `~/.config/opencode` real
- Nenhum teste modifica o `~/.bashrc` real
- Cada teste começa com estado limpo
- Cleanup automático mesmo em falha

---

## 5. Estrutura Proposta de Diretórios

```
tests/
├── bats-libs/              # git submodules
│   ├── bats-core/
│   ├── bats-assert/
│   └── bats-file/
├── fixtures/               # arquivos de teste
│   ├── sample.pdf
│   ├── sample.md
│   ├── sample.svg
│   └── pre-existing-config/
├── helpers/
│   └── test_helper.bash    # setup/teardown compartilhado
├── bootstrap/
│   ├── opencode-link.bats
│   └── opencode-install-deps.bats
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
└── smoke.bats              # teste end-to-end rápido
```

---

## 6. Plano de Implementação em Etapas

### Etapa 1 — Infraestrutura de Testes

**O quê:** Instalar BATS e criar estrutura base.

- Adicionar `bats-core`, `bats-assert` e `bats-file` como git submodules em
  `tests/bats-libs/`
- Criar `tests/helpers/test_helper.bash` com:
  - Funções `setup()`/`teardown()` com sandbox
  - Carregamento das libs
  - Variáveis de caminho comuns
- Criar `Makefile` na raiz com targets:
  - `make test` — roda todos os testes
  - `make test-unit` — só testes unitários
  - `make test-integration` — só testes de integração
  - `make test-smoke` — só smoke test
- Criar 1 teste trivial para validar que a infra funciona
- Atualizar `.gitignore` se necessário

**Entregável:** `bats tests/` funciona e exibe 1 teste passando.

---

### Etapa 2 — Testes de Estrutura Estática

**O quê:** Validar que o repo tem a estrutura esperada.

- `tests/structure/repo-structure.bats`:
  - Arquivos obrigatórios existem
  - Cada skill tem `SKILL.md`
  - `opencode.json` é JSON válido
  - Agentes têm frontmatter válido
  - Scripts são executáveis (`-x`)
- Esses testes rodam sem dependências externas

**Entregável:** ~15-20 testes de estrutura.

---

### Etapa 3 — Testes do Bootstrap (`opencode-link`)

**O quê:** Testar o fluxo principal do repo.

- `tests/bootstrap/opencode-link.bats`:
  - Execução com `--yes` em sandbox
  - Validação dos 6 symlinks (`assert_symlink_to`)
  - Idempotência (rodar 2×)
  - Backup de configs pré-existentes
  - `.bashrc` contém `OPENCODE_ENABLE_EXA=1`
  - Sem duplicatas no `.bashrc` após 2ª execução
  - `--help` retorna 0
  - Opção inválida retorna 2

**Entregável:** ~10-15 testes do bootstrap.

---

### Etapa 4 — Testes do `opencode-install-deps`

**O quê:** Testar detecção de deps e formatação de saída.

- `tests/bootstrap/opencode-install-deps.bats`:
  - `--help` retorna 0
  - `--quiet` suprime saída
  - Detecção de OS funciona
  - Com dependência presente → exibe `OK`
  - Com dependência ausente → exibe `MISSING` + hint

**Entregável:** ~8-10 testes.

---

### Etapa 5 — Refatoração do `install-crawl4ai-mcp.sh` + Testes

**O quê:** Restringir o script à sua única responsabilidade real e testar.

**Problema identificado:** O script hoje cria arquivos diretamente em
`~/.config/opencode/` (`opencode.json`, `AGENTS.md`, `scripts/crawl4ai/`), assumindo
que é o instalador de toda a config do OpenCode. Isso conflita com a abordagem deste
repo: o `opencode-link` já gerencia esses caminhos via symlinks; qualquer escrita direta
quebra o vínculo com o repo.

Além disso, o `opencode.json` deste repo **já inclui** a config do MCP do Crawl4AI.
Portanto o instalador não precisa criar essa config — ela já existe via symlink.

**Refatoração:** O script deve ficar responsável apenas por:

1. Verificar que Docker está instalado e em execução
2. Fazer pull da imagem `unclecode/crawl4ai:latest`
3. Fazer build da imagem `crawl4ai-sanitized:latest`
4. Garantir o bloco de auto-start no `~/.bashrc` (idempotente, com markers)
5. Iniciar o container pela primeira vez

Tudo que hoje cria arquivos em `~/.config/opencode/` deve ser **removido** do script.

**Testes** (`tests/crawl4ai/install-crawl4ai-mcp.bats`):

- Docker indisponível → aborta com erro
- Não cria nem modifica nenhum arquivo em `~/.config/opencode/`
- Adiciona bloco com markers no `.bashrc` do sandbox
- Sem duplicata ao rodar 2×

**Entregável:** Script refatorado + ~5-8 testes.

---

### Etapa 6 — Testes dos Wrappers de Skills

**O quê:** Validar execução real dos wrappers com ferramentas reais instaladas.

- `tests/wrappers/doc-extract.bats`:
  - Entrada válida (PDF fixture) → JSON `ok:true`, artifact existe
  - Sem campo `source` → JSON `ok:false`
  - Formato inválido → JSON `ok:false`
  - Sem `docling` no PATH → JSON `ok:false` com hint

- `tests/wrappers/md-export.bats`:
  - MD fixture → DOCX gerado, JSON `ok:true`
  - Sem `source` → `ok:false`
  - Formato inválido → `ok:false`
  - Arquivo já existe sem `--overwrite` → `ok:false`
  - Sem `pandoc` → `ok:false` com hint

- `tests/wrappers/svgtoimage.bats`:
  - SVG fixture via stdin → JSON com `imagePath`, PNG existe
  - Sem conversor → exit 1

**Entregável:** ~20-25 testes de integração com ferramentas reais.

---

### Etapa 7 — Testes dos Scripts Auxiliares de Skills

**O quê:** Validar scripts de gerenciamento de skills.

- `tests/skills/list-updatable.bats`:
  - Saída coerente com skills que têm `UPSTREAM.md`
  - Ordem alfabética

- `tests/skills/update-upstream-skill.bats`:
  - `--help` funciona
  - Skill inexistente → erro
  - (Teste de sync real é opcional/CI-only por depender de rede)

**Entregável:** ~5-8 testes.

---

### Etapa 8 — Smoke Test E2E + GitHub Actions CI

**O quê:** Teste de ponta a ponta e integração contínua.

- `tests/smoke.bats`:
  - Executa `opencode-link --yes` em sandbox
  - Valida TODOS os symlinks
  - Valida `.bashrc`
  - Valida que `opencode.json` no destino é legível e válido
  - Valida que skills são acessíveis via symlink

- `.github/workflows/test.yml`:
  - Trigger: `push` e `pull_request`
  - Runner: `ubuntu-latest`
  - Steps:
    1. Checkout com submodules
    2. Instalar dependências (pandoc, librsvg2-bin, pipx, docling)
    3. `make test`
  - Artefatos: output TAP para summary do PR

**Entregável:** CI funcionando, badge no README.

---

## 7. Estratégia de Evolução e Prevenção de Regressão

### 7.1 Convenção para novas funcionalidades

Toda nova funcionalidade DEVE incluir testes:

- **Novo script** → arquivo `.bats` correspondente em `tests/<categoria>/`
- **Nova skill** → teste de estrutura (tem `SKILL.md`) coberto automaticamente pelo
  teste glob existente; se tiver script wrapper, adicionar teste de integração
- **Novo agente** → coberto pelo teste glob de `agents/`
- **Novo symlink no bootstrap** → adicionar ao teste de `opencode-link.bats`

### 7.2 Regressão

- O `make test` roda TODOS os testes (unitários + integração + smoke)
- GitHub Actions bloqueia merge se testes falham
- Testes existentes NUNCA são removidos, apenas evoluídos
- O smoke test cobre o fluxo completo e captura regressões que testes unitários não
  pegariam

### 7.3 Execução local sob demanda

```bash
# Todos os testes
make test

# Só estrutura (rápido, sem deps externas)
make test-unit

# Só wrappers (precisa de pandoc, docling, resvg)
make test-integration

# Só smoke test
make test-smoke

# Um arquivo específico
./tests/bats-libs/bats-core/bin/bats tests/bootstrap/opencode-link.bats
```

---

## 8. Riscos e Trade-offs

| Item | Risco/Trade-off | Mitigação |
|------|-----------------|-----------|
| Deps externas nos testes de integração | Testes falham se pandoc/docling/resvg não instalados | Separar em `make test-integration`; CI instala tudo |
| Docker nos testes de Crawl4AI | CI pode não ter Docker facilmente | Testar apenas a lógica de verificação (Docker check), não o container real |
| Fixtures de PDF | Aumenta tamanho do repo com binário | Usar PDF mínimo (1 página, ~5KB); commitar em `tests/fixtures/` |
| `opencode-install-deps` tenta instalar coisas | Efeito colateral em testes | Sandbox + mock do PATH para simular ausência/presença de deps |

### Decisões fechadas

| # | Decisão | Resolução |
|---|---------|-----------|
| 1 | `install-crawl4ai-mcp.sh`: o que fazer com `opencode.json` e `AGENTS.md` | Script só altera `~/.bashrc`; config do MCP já existe no repo via `opencode.json` |
| 2 | Fixture de PDF: commitar ou gerar? | Commitar PDF mínimo em `tests/fixtures/sample.pdf` |
| 3 | Coverage com `kcov` | Fora do escopo inicial |

---

## 9. Recomendação Final

| Aspecto | Decisão |
|---------|---------|
| Framework | BATS-core + bats-assert + bats-file |
| Instalação | Git submodules em `tests/bats-libs/` |
| Isolamento | Sandbox em `/tmp` com `$HOME` redirecionado |
| Execução local | `make test` (Makefile na raiz) |
| CI | GitHub Actions, `ubuntu-latest` |
| Ordem de implementação | Etapas 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 |

**Estimativa de esforço por etapa:**

| Etapa | Complexidade | ~Testes |
|-------|-------------|---------|
| 1. Infraestrutura | Baixa | 1 |
| 2. Estrutura estática | Baixa | 15–20 |
| 3. Bootstrap | Média | 10–15 |
| 4. Install-deps | Média | 8–10 |
| 5. Crawl4AI refatoração + testes | Média | 5–8 |
| 6. Wrappers | Alta | 20–25 |
| 7. Scripts auxiliares | Baixa | 5–8 |
| 8. Smoke + CI | Média | 5–10 |
| **Total** | | **~70–97 testes** |

---

## Apêndice: Exemplo de Teste

```bash
#!/usr/bin/env bats
# tests/bootstrap/opencode-link.bats

load "../helpers/test_helper"

setup() {
  common_setup  # cria sandbox, exporta HOME
}

teardown() {
  common_teardown  # remove sandbox
}

@test "opencode-link --yes cria diretório ~/.config/opencode" {
  run bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_success
  assert_dir_exist "$TEST_CONFIG_DIR"
}

@test "opencode-link --yes cria symlink para AGENTS.md" {
  run bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_success
  assert_symlink_to "$TEST_CONFIG_DIR/AGENTS.md" \
    "$REPO_ROOT/AGENTS.md"
}

@test "opencode-link é idempotente" {
  bash "$REPO_ROOT/scripts/opencode-link" --yes
  run bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_success
  # Sem diretório de backup criado na 2ª execução
}

@test "opencode-link faz backup de config pré-existente" {
  mkdir -p "$TEST_CONFIG_DIR"
  echo "old" > "$TEST_CONFIG_DIR/AGENTS.md"
  run bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_success
  assert_dir_exist "$TEST_HOME/.config/opencode-backup"
}

@test "opencode-link adiciona OPENCODE_ENABLE_EXA=1 ao .bashrc" {
  run bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_success
  run grep "OPENCODE_ENABLE_EXA=1" "$TEST_BASHRC"
  assert_success
}
```
