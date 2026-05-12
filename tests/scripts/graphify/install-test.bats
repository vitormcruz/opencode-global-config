#!/usr/bin/env bats
# tests/scripts/graphify/install-test.bats

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/graphify/install"

setup()    { common_setup; }
teardown() { common_teardown; }

# ---------------------------------------------------------------------------
# --help retorna exit 0
# ---------------------------------------------------------------------------

@test "install --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "install"
}

@test "install -h exibe texto de uso" {
  run bash "$SCRIPT" -h
  assert_success
  assert_output --partial "Uso:"
}

# ---------------------------------------------------------------------------
# Opcao desconhecida -> exit 2
# ---------------------------------------------------------------------------

@test "install opcao desconhecida retorna exit 2" {
  run bash "$SCRIPT" --opcao-inexistente
  assert_failure 2
  assert_output --partial "desconhecida"
}

# ---------------------------------------------------------------------------
# --check-only sem graphify no PATH -> exit 1, MISSING
# ---------------------------------------------------------------------------

@test "install --check-only sem graphify reporta MISSING" {
  local fake_bin
  fake_bin="$(mktemp -d)"
  ln -s "$(command -v bash)" "$fake_bin/bash"

  run env PATH="$fake_bin" bash "$SCRIPT" --check-only
  assert_failure
  assert_output --partial "MISSING"
}

# ---------------------------------------------------------------------------
# --check-only com graphify disponivel -> exit 0, OK
# ---------------------------------------------------------------------------

@test "install --check-only com graphify reporta OK" {
  if ! command -v graphify >/dev/null 2>&1; then
    skip "graphify nao instalado"
  fi

  run bash "$SCRIPT" --check-only
  assert_success
  assert_output --partial "OK"
}
