# Plan: Consolidar instalação do mcp (avelino) no Bash + remover do PowerShell

**TL;DR**: Instalação do `mcp` fica 100% no `opencode-install-deps.sh` (já
implementado com SHA configurável e erro orientado). Remover `Install-McpWrapper`
do `vscode-sync.ps1`, ajustar testes e README.

---

## Estado atual

O bloco mcp (avelino) em `opencode-install-deps.sh` (linhas 572-651) **já possui**:
- `$MCP_EXPECTED_SHA` configurável via variável de ambiente
- Exibição de SHA esperado + SHA real quando não batem
- Mensagem orientada ao humano com instruções de atualização
- Remoção do binário inválido em caso de SHA mismatch

O `vscode-sync.ps1` ainda contém `Install-McpWrapper` (instala `mcp.exe` no
Windows) — deve ser removido pois a instalação é exclusiva do ambiente WSL/Linux.

---

## O que falta fazer

### Modificação 1 — Remover `Install-McpWrapper` do vscode-sync.ps1

**Arquivo**: `scripts/bootstrap_repo/vscode-sync.ps1`

Remover:
- Bloco de comentário + função `Install-McpWrapper` (linhas ~373-410)
- Chamada `Install-McpWrapper` no fluxo principal (linha ~536)
- Menção a "wrapper MCP" em `Show-Usage`

### Modificação 2 — Testes

**Criar** novos testes em `tests/scripts/bootstrap_repo/opencode-install-deps-test.bats`:

8 novos `@test` usando mocks em `fake_bin` (mesmo padrão dos testes existentes
de `doctree-mcp` e `codebase-memory-mcp`):

| T # | Descrição |
|---|---|
| T1 | `mcp` já instalado no PATH → `status_ok` e pular |
| T2 | `mcp` ausente + sem `curl` → `status_missing` com hint de curl |
| T3 | SHA OK (mock de `curl` + `sha256sum`) → instala em `~/.local/bin/mcp` |
| T4 | SHA incorreto → aborta + exibe **ambos** SHAs + guidance |
| T5 | `$MCP_EXPECTED_SHA` sobrescrito via env var funciona |
| T6 | SHA calculado é exibido no output (transparência) |
| T7 | Fallback sem `jq` (o script usa `/latest/download/` direto, sem `jq`) |
| T8 | Binário instalado é executável (`-x`) |

**Remover** testes obsoletos em `tests/scripts/bootstrap_repo/vscode-sync-test.bats`:
- `vscode-sync: contem funcao Install-McpWrapper`
- `vscode-sync: Install-McpWrapper referencia URL de download do avelino/mcp`
- `vscode-sync: Install-McpWrapper e chamado antes de Sync-Instructions`
- `vscode-sync: Show-Usage menciona wrapper MCP e copilot-instructions`

### Modificação 3 — README

**Arquivo**: `README.md`

Remover:
- Linha 109: `Instala \`mcp (avelino)\` → \`%LOCALAPPDATA%\bin\mcp.exe\` (wrapper
  CLI para MCP)`
- Parágrafo linhas 116-117: `O \`vscode-sync.ps1\` instala automaticamente o
  binário do wrapper \`mcp (avelino)\` em \`%LOCALAPPDATA%\bin\\\` e garante que o
  diretório esteja no \`PATH\`.`

(A linha 67 já lista `mcp (avelino)` nas deps instaladas automaticamente — OK.)

---

## Já implementado (referência)

| Item | Onde |
|---|---|
| SHA configurável via `$MCP_EXPECTED_SHA` | `opencode-install-deps.sh` L576 |
| Erro orientado com ambos SHAs + guidance | `opencode-install-deps.sh` L625-641 |
| Exibição do SHA calculado (transparência) | `opencode-install-deps.sh` L618-619 |
| `fix_mcp_block.py` removido | Já não existe |
| Bug `ay ""` corrigido | Já não existe |
| Comentário SHA desatualizado removido | Já não existe |

---

## Arquivos modificados

| Arquivo | O que |
|---|---|
| `scripts/bootstrap_repo/vscode-sync.ps1` | Remover `Install-McpWrapper` + chamada + menção em `Show-Usage` |
| `tests/scripts/bootstrap_repo/opencode-install-deps-test.bats` | Criar 8 novos testes para `mcp (avelino)` |
| `tests/scripts/bootstrap_repo/vscode-sync-test.bats` | Remover 4 testes de `Install-McpWrapper` |
| `README.md` | Remover referências à instalação Windows do mcp |

---

## Decisões

| Decisão | Justificativa |
|---|---|
| URL `/latest/download/` mantido | `curl -fsSL` com `-L` já segue redirects |
| SHA esperado configurável via env var | Permite atualizar sem editar o script |
| Erro orienta o humano | Mostra SHA esperado + SHA real + 2 opções |
| Instalação exclusiva no Bash script | MCP é Linux-ELF, usado via WSL |
| Remover do PowerShell | Elimina duplicidade, centraliza no Bash |
| Mocks nos testes | fake_bin com `curl` e `sha256sum` mockados — sem rede |
