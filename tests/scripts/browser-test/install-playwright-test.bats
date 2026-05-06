#!/usr/bin/env bats
# tests/scripts/browser-test/install-playwright-test.bats

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/browser-test/install-playwright.sh"

setup()    { common_setup; }
teardown() { common_teardown; }

# ---------------------------------------------------------------------------
# --help retorna exit 0
# ---------------------------------------------------------------------------

@test "install-playwright --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "install-playwright"
}

@test "install-playwright -h retorna exit 0" {
  run bash "$SCRIPT" -h
  assert_success
  assert_output --partial "Uso:"
}

# ---------------------------------------------------------------------------
# Opcao desconhecida → exit 2
# ---------------------------------------------------------------------------

@test "install-playwright opcao desconhecida retorna exit 2" {
  run bash "$SCRIPT" --foo
  assert_failure 2
  assert_output --partial "desconhecida"
}

# ---------------------------------------------------------------------------
# --check-only com playwright ausente → exit 1, Status: MISSING
# ---------------------------------------------------------------------------

@test "install-playwright --check-only sem playwright reporta MISSING" {
  # Cria PATH fake sem node/npx
  local fake_bin
  fake_bin="$(mktemp -d)"
  # Coloca apenas bash no fake bin
  ln -s "$(command -v bash)" "$fake_bin/bash"

  run env PATH="$fake_bin" bash "$SCRIPT" --check-only
  assert_failure
  assert_output --partial "MISSING"
}

# ---------------------------------------------------------------------------
# --check-only com node e playwright → exit 0, Status: OK
# ---------------------------------------------------------------------------

@test "install-playwright --check-only com node e playwright reporta OK" {
  # bats test_tags=requires:playwright
  if ! command -v node >/dev/null 2>&1; then
    skip "node nao disponivel no PATH"
  fi
  if ! command -v playwright >/dev/null 2>&1; then
    skip "playwright nao instalado"
  fi

  run bash "$SCRIPT" --check-only
  assert_success
  assert_output --partial "OK"
}
