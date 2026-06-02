#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/vscode-sync-test.bats — valida vscode-sync.ps1

load "../../helpers/test_helper"

# ---------------------------------------------------------------------------
# .github/copilot-specific.instructions.md — arquivo versionado e independente
# ---------------------------------------------------------------------------

@test "vscode-sync: .github/copilot-specific.instructions.md existe no repo" {
  assert_file_exist "$REPO_ROOT/.github/copilot-specific.instructions.md"
}

@test "vscode-sync: copilot-specific.instructions.md NAO e copia identica do AGENTS.md" {
  run diff "$REPO_ROOT/.github/copilot-specific.instructions.md" "$REPO_ROOT/AGENTS.md"
  assert_failure
}

@test "vscode-sync: copilot-specific.instructions.md instrui uso do comando mcp" {
  run grep -qE "Use o comando .mcp.|comando \`mcp\`" "$REPO_ROOT/.github/copilot-specific.instructions.md"
  assert_success
}

@test "vscode-sync: copilot-specific.instructions.md contem secao MCP via CLI" {
  run grep -q "MCP via CLI" "$REPO_ROOT/.github/copilot-specific.instructions.md"
  assert_success
}

@test "vscode-sync: copilot-specific.instructions.md referencia servidor crawl4ai" {
  run grep -c "crawl4ai" "$REPO_ROOT/.github/copilot-specific.instructions.md"
  assert_success
  [[ "$output" -ge 2 ]]
}

@test "vscode-sync: copilot-specific.instructions.md menciona que regras gerais estao no AGENTS.md" {
  run grep -q "AGENTS.md" "$REPO_ROOT/.github/copilot-specific.instructions.md"
  assert_success
}

@test "vscode-sync: copilot-specific.instructions.md define applyTo global" {
  run grep -q 'applyTo: "\*\*"' "$REPO_ROOT/.github/copilot-specific.instructions.md"
  assert_success
}

# ---------------------------------------------------------------------------
# vscode-sync.ps1 — estrutura e funcoes
# ---------------------------------------------------------------------------

@test "vscode-sync: script existe no repo" {
  assert_file_exist "$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1"
}

@test "vscode-sync: Sync-Instructions copia de .github/copilot-specific.instructions.md" {
  run bash -c "grep -A 12 '^function Sync-Instructions' '$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1' | grep -q 'copilot-specific.instructions.md'"
  assert_success
}

@test "vscode-sync: Sync-Instructions copia para .copilot/instructions" {
  run bash -c "grep -A 12 '^function Sync-Instructions' '$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1' | grep -q '\\.copilot\\\\instructions'"
  assert_success
}

@test "vscode-sync: Sync-Instructions NAO referencia AGENTS.md como fonte" {
  run bash -c "grep -A 12 '^function Sync-Instructions' '$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1' | grep -q 'AGENTS.md'"
  assert_failure
}

@test "vscode-sync: Show-Plan NAO menciona copia de AGENTS.md para instructions" {
  run bash -c "grep -A 12 '^    Say \"Plano:\"' '$REPO_ROOT/scripts/bootstrap_repo/vscode-sync.ps1' | grep -q 'AGENTS.md'"
  assert_failure
}
