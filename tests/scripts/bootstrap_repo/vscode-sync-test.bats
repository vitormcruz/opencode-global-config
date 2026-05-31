#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/vscode-sync-test.bats — valida vscode-sync.ps1

load "../../helpers/test_helper"

# ---------------------------------------------------------------------------
# .github/copilot-instructions.md — arquivo versionado e independente
# ---------------------------------------------------------------------------

@test "vscode-sync: .github/copilot-instructions.md existe no repo" {
  assert_file_exist "$REPO_ROOT/.github/copilot-instructions.md"
}

@test "vscode-sync: copilot-instructions.md NAO e copia identica do AGENTS.md" {
  run diff "$REPO_ROOT/.github/copilot-instructions.md" "$REPO_ROOT/AGENTS.md"
  assert_failure
}

@test "vscode-sync: copilot-instructions.md instrui uso do comando mcp" {
  run grep -qE "Use o comando .mcp.|comando \`mcp\`" "$REPO_ROOT/.github/copilot-instructions.md"
  assert_success
}

@test "vscode-sync: copilot-instructions.md contem secao MCP via CLI" {
  run grep -q "MCP via CLI" "$REPO_ROOT/.github/copilot-instructions.md"
  assert_success
}

@test "vscode-sync: copilot-instructions.md referencia servidor crawl4ai" {
  run grep -c "crawl4ai" "$REPO_ROOT/.github/copilot-instructions.md"
  assert_success
  [[ "$output" -ge 2 ]]
}

@test "vscode-sync: copilot-instructions.md menciona que regras gerais estao no AGENTS.md" {
  run grep -q "AGENTS.md" "$REPO_ROOT/.github/copilot-instructions.md"
  assert_success
}

# ---------------------------------------------------------------------------
# vscode-sync.ps1 — estrutura e funcoes
# ---------------------------------------------------------------------------

@test "vscode-sync: script existe no repo" {
  assert_file_exist "$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1"
}

@test "vscode-sync: contem funcao Install-McpWrapper" {
  run grep -c "^function Install-McpWrapper" "$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1"
  assert_success
  [[ "$output" -eq 1 ]]
}

@test "vscode-sync: Install-McpWrapper referencia URL de download do avelino/mcp" {
  run grep -q "github.com/avelino/mcp/releases" "$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1"
  assert_success
}

@test "vscode-sync: Sync-Instructions copia de .github/copilot-instructions.md (nao de AGENTS.md)" {
  run bash -c "grep -A 10 '^function Sync-Instructions' '$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1' | grep -q '.github'"
  assert_success
}

@test "vscode-sync: Sync-Instructions NAO referencia AGENTS.md como fonte" {
  run bash -c "grep -A 10 '^function Sync-Instructions' '$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1' | grep -q 'AGENTS.md'"
  assert_failure
}

@test "vscode-sync: Install-McpWrapper e chamado antes de Sync-Instructions no fluxo principal" {
  run bash -c "grep -A 20 '^Show-Plan' '$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1' | grep -n 'Install-McpWrapper\|Sync-Instructions'"
  assert_success
  local install_line sync_line
  install_line=$(echo "$output" | grep "Install-McpWrapper" | head -1 | cut -d: -f1)
  sync_line=$(echo "$output"    | grep "Sync-Instructions"   | head -1 | cut -d: -f1)
  [[ "$install_line" -lt "$sync_line" ]]
}

@test "vscode-sync: Show-Usage menciona wrapper MCP e copilot-instructions" {
  run bash -c "grep -A 20 '^function Show-Usage' '$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1' | grep -q 'wrapper MCP'"
  assert_success
  run bash -c "grep -A 20 '^function Show-Usage' '$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1' | grep -q 'copilot-instrs'"
  assert_success
}

@test "vscode-sync: Show-Plan NAO menciona copia de AGENTS.md para copilot-instructions" {
  run bash -c "grep -A 10 '^    Say \"Plano:\"' '$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1' | grep -q 'AGENTS.md'"
  assert_failure
}
