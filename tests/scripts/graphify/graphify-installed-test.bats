#!/usr/bin/env bats
# tests/scripts/graphify/graphify-installed-test.bats
# Verifica que o graphify esta instalado e funcional no WSL.
# Requer ferramenta instalada — rode com: make test-tools

load "../../helpers/test_helper"

setup()    { common_setup; }
teardown() { common_teardown; }

# ---------------------------------------------------------------------------
# graphify esta no PATH e responde a --version
# ---------------------------------------------------------------------------

@test "graphify esta instalado e acessivel no PATH" {
  run command -v graphify
  assert_success
}

@test "graphify --version retorna exit 0" {
  run graphify --version
  assert_success
}
