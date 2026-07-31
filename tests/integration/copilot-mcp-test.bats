#!/usr/bin/env bats
# tests/integration/copilot-mcp-test.bats — smoke tests MCP via avelino/mcp

load "../helpers/test_helper"

setup() {
  common_setup
}

teardown() {
  common_teardown
}

# ---------------------------------------------------------------------------
# Smoke: mcp CLI operacoes basicas
# ---------------------------------------------------------------------------

@test "copilot-mcp: mcp add sem argumentos exibe usage" {
  if ! command -v mcp >/dev/null 2>&1; then
    fail "mcp CLI nao encontrado. Instale via bootstrap: ./scripts/bootstrap_repo/configurar-repo.sh --yes"
  fi
  run mcp add
  assert_failure
  assert_output --partial "usage"
}

@test "copilot-mcp: mcp remove sem argumentos exibe usage" {
  if ! command -v mcp >/dev/null 2>&1; then
    fail "mcp CLI nao encontrado. Instale via bootstrap: ./scripts/bootstrap_repo/configurar-repo.sh --yes"
  fi
  run mcp remove
  assert_failure
  assert_output --partial "usage"
}

@test "copilot-mcp: mcp sem argumentos exibe help" {
  if ! command -v mcp >/dev/null 2>&1; then
    fail "mcp CLI nao encontrado. Instale via bootstrap: ./scripts/bootstrap_repo/configurar-repo.sh --yes"
  fi
  run mcp
  assert_success
  assert_output --partial "Usage"
}

@test "copilot-mcp: mcp com servidor inexistente reporta erro" {
  if ! command -v mcp >/dev/null 2>&1; then
    fail "mcp CLI nao encontrado. Instale via bootstrap: ./scripts/bootstrap_repo/configurar-repo.sh --yes"
  fi
  run timeout 5 mcp servidor_inexistente_xyz --list
  assert_failure
}
