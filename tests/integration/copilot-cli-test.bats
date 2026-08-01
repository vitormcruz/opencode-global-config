#!/usr/bin/env bats
# tests/integration/copilot-cli-test.bats — smoke tests do Copilot CLI

load "../helpers/test_helper"

# Salva HOME real antes do common_setup sobrescrever
REAL_HOME="$HOME"

setup() {
  common_setup
  mkdir -p "$HOME/.config/mcp"
  if [ -f "$REAL_HOME/.config/mcp/servers.json" ]; then
    cp "$REAL_HOME/.config/mcp/servers.json" "$HOME/.config/mcp/servers.json"
  fi
}

teardown() {
  common_teardown
}

# ---------------------------------------------------------------------------
# Smoke: CLI existe e funcional
# ---------------------------------------------------------------------------

@test "copilot-cli: copilot --help retorna exit 0" {
  if ! command -v copilot >/dev/null 2>&1; then
    fail "copilot CLI nao encontrado. Instale: npm install -g @github/copilot && copilot --login"
  fi
  run copilot --help
  assert_success
}

@test "copilot-cli: copilot --version exibe versao" {
  if ! command -v copilot >/dev/null 2>&1; then
    fail "copilot CLI nao encontrado. Instale: npm install -g @github/copilot && copilot --login"
  fi
  run copilot --version
  assert_success
  assert_output --regexp '[0-9]+\.[0-9]+'
}

# ---------------------------------------------------------------------------
# Smoke: MCP wrapper (avelino/mcp)
# ---------------------------------------------------------------------------

@test "copilot-cli: mcp --help retorna exit 0" {
  if ! command -v mcp >/dev/null 2>&1; then
    fail "mcp CLI nao encontrado. Instale via bootstrap: ./scripts/bootstrap_repo/configurar-repo.sh --yes"
  fi
  run mcp --help
  assert_success
}

@test "copilot-cli: mcp --list retorna exit 0 e output contem JSON" {
  if ! command -v mcp >/dev/null 2>&1; then
    fail "mcp CLI nao encontrado. Instale via bootstrap: ./scripts/bootstrap_repo/configurar-repo.sh --yes"
  fi
  run timeout 30 mcp --list
  assert_success
  assert_output --partial ']'
  assert_output --partial "crawl4ai"
  assert_output --partial "codebase-memory"
  assert_output --partial "doctree"
}
