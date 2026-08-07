#!/usr/bin/env bats
# tests/integration/copilot-cli-test.bats — smoke tests do Copilot CLI

load "../helpers/test_helper"

setup() {
  common_setup
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
