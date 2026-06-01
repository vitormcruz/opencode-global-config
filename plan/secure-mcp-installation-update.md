# Plan: Mover atualização de SHA do mcp (avelino) → erro orientado ao humano

**TL;DR**: O script baixa o binário do `latest/download/` (que segue redirects sozinho), mas tem SHA hardcoded que quebra a cada release. Solução: exibir SHA esperado + SHA real quando não bater, instruindo o humano a atualizar. Tornar `$MCP_EXPECTED_SHA` configurável via variável de ambiente.

**O mcp é instalado SOMENTE pelo Bash script (`opencode-install-deps.sh`).** Zero alteração no PowerShell script.

---

### Problema atual

O bloco mcp (avelino) em `opencode-install-deps.sh` linha 528–554 tem SHA-256 hardcoded:
```
SHA esperado no repo: 1820c6f48ce02a13f8176dd4f30d41614b29525216a50a83ddef17ba79fc11dd
```

Quando o upstream lança nova versão, o binário muda → SHA não bate → instalação falha.
O script atual mostra apenas "SHA expected:" — não diz o que o humano deve fazer.

---

### O que vai mudar

#### Modificação 1 — Erro orientado ao humano

**Arquivo**: `scripts/bootstrap_repo/opencode-install-deps.sh`

Quando SHA não bater, exibir:
```
[SHA mismatch]
  SHA esperado no repo: 1820c6f48ce02a13f8176dd4f30d41614b29525216a50a83ddef17ba79fc11dd
  SHA real (arquivo):   abcdef1234567890...novohash

  O upstream mudou o binario. Atualize MCP_EXPECTED_SHA.

  Para atualizar agora (temporario):
    MCP_EXPECTED_SHA="abcdef1234567890..." ./scripts/bootstrap_repo/opencode-install-deps.sh --yes

  Para atualizar permanentemente, edite a variavel MCP_EXPECTED_SHA
  em scripts/bootstrap_repo/opencode-install-deps.sh
```

#### Modificação 2 — `$MCP_EXPECTED_SHA` configurável via variável de ambiente

```bash
# Linha ~537 — substituir
MCP_EXPECTED_SHA="${MCP_EXPECTED_SHA:-1820c6f48ce02a13f8176dd4f30d41614b29525216a50a83ddef17ba79fc11dd}"
```

O humano pode rodar sem editar o script:
```bash
MCP_EXPECTED_SHA="novohash" ./scripts/bootstrap_repo/opencode-install-deps.sh --yes
```

#### Modificação 3 — Mostrar SHA calculado no terminal (transparência)

Ao calcular o SHA-256 do arquivo baixado, mostrar no terminal:
```
Calculando SHA-256 do arquivo baixado...
SHA: abcdef1234567890...
```

#### Modificação 4 — Bug fix

Linha 550: trocar `ay ""` por `say ""`.

#### Modificação 5 — Remover comentário desatualizado

Remover: `# SHA-256 do release atual — atualizar manualmente quando houver novo release`
(Substituir pela nova UX de erro orientado, já discutida acima.)

#### Modificação 6 — Limpeza

- Remover `scripts/bootstrap_repo/fix_mcp_block.py` (arquivo órfão, patcher abandonado, nunca referenciado).

#### Modificação 7 — Testes

**Criar** novos testes em `tests/scripts/bootstrap_repo/opencode-install-deps-test.bats`:

8 novos `@test` usando mocks em `fake_bin` (mesmo padrão dos testes existentes de `doctree-mcp` e `codebase-memory-mcp`):

| T # | Descrição |
|---|---|
| T1 | `mcp` já instalado no PATH → `status_ok` e pular |
| T2 | `mcp` ausente + sem `curl` → `status_missing` com hint de curl |
| T3 | SHA OK (mock de `curl` + `sha256sum`) → instala em `~/.local/bin/mcp` |
| T4 | SHA incorreto → aborta + exibe **ambos** SHAs + guidance |
| T5 | `$MCP_EXPECTED_SHA` sobrescrito via env var funciona |
| T6 | SHA calculado é exibido no output (transparência) |
| T7 | Fallback sem `jq` (o script usa `/latest/download/` direto, sem `jq` — verificar que funciona) |
| T8 | Binário instalado é executável (`-x`) |

**Remover** testes quebrados em `tests/scripts/bootstrap_repo/vscode-sync-test.bats`:
- `vscode-sync: contem funcao Install-McpWrapper`
- `vscode-sync: Install-McpWrapper referencia URL de download do avelino/mcp`
- `vscode-sync: Install-McpWrapper e chamado antes de Sync-Instructions`
- `vscode-sync: Show-Usage menciona wrapper MCP e copilot-instructions`

#### Modificação 8 — README

**Arquivo**: `README.md`

Remover:
- Linha `Instala \`mcp (avelino)\` → \`%LOCALAPPDATA%\bin\mcp.exe\` (wrapper CLI para MCP)`
- Parágrafo `O \`vscode-sync.ps1\` instala automaticamente...`

Adicionar:
- `mcp (avelino)` à lista de deps instaladas automaticamente (ao lado de bats, pipx, codebase-memory-mcp, etc.)

---

### Flow quando SHA não bate

```
[1] Script baixa arquivo de /latest/download/ (curl -fsSL, -L segue redirects)
[2] Calcula sha256sum do arquivo baixado
[3] Compara com $MCP_EXPECTED_SHA
[4] Se não bater:
    → Mostra:
        SHA esperado no repo: 123abc... (hardcoded)
        SHA real do arquivo:   456def... (calculado)
    → Instrução clara:
        Para atualizar agora (temporario): MCP_EXPECTED_SHA='456def...' ./scripts/...
        Para atualizar permanentemente: edite opencode-install-deps.sh
```

---

### Arquivos modificados

| Arquivo | O que |
|---|---|
| `scripts/bootstrap_repo/opencode-install-deps.sh` | SHA configurável, exibição de SHA real, erro orientado, bug `ay ""` |
| `tests/scripts/bootstrap_repo/opencode-install-deps-test.bats` | Criar 8 novos testes para `mcp (avelino)` |
| `tests/scripts/bootstrap_repo/vscode-sync-test.bats` | Remover 4 testes da função `Install-McpWrapper` (nunca existiu) |
| `README.md` | Corrigir referência falsa, adicionar mcp à lista de instaladas |
| `scripts/bootstrap_repo/fix_mcp_block.py` | Remover (órfão) |

---

### Decisões

| Decisão | Justificativa |
|---|---|
| URL `/latest/download/` mantido | `curl -fsSL` com `-L` já segue redirecionamentos — não precisa API |
| SHA esperado configurável via env var | Permite atualizar sem editar o script |
| Erro orienta o humano | Mostra SHA esperado + SHA real + 2 opções (temporario vs permanente) |
| Instalação no Bash script apenas | MCP é Linux-ELF, usado via WSL |
| Mocks nos testes | fake_bin com `curl` e `sha256sum` mockados — sem dependência de rede |
