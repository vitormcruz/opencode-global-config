#!/usr/bin/env bats
# tests/scripts/codebase-memory/install-codebase-memory-test.bats
# Testa o script scripts/codebase-memory/install

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/codebase-memory/install"

setup()    { common_setup; }
teardown() { common_teardown; }

@test "codebase-memory/install --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "codebase-memory/install"
  assert_output --partial "Uso:"
}

@test "codebase-memory/install com opcao invalida retorna exit 2" {
  run bash "$SCRIPT" --opcao-inexistente
  assert_failure
  [ "$status" -eq 2 ]
}

@test "codebase-memory/install --check-only reporta que binario ja esta instalado" {
  local fake_bin
  fake_bin="$(mktemp -d)"
  printf '#!/bin/sh\necho "codebase-memory-mcp 1.0.0"\n' > "$fake_bin/codebase-memory-mcp"
  chmod +x "$fake_bin/codebase-memory-mcp"

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --check-only
  assert_success
  assert_output --partial "ja instalado"

  rm -rf "$fake_bin"
}

@test "codebase-memory/install --check-only reporta MISSING quando binario ausente" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --check-only
  assert_success
  assert_output --partial "nao encontrado no PATH"

  rm -rf "$fake_bin"
}

@test "codebase-memory/install aborta quando npm nao esta disponivel" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --yes
  assert_failure
  assert_output --partial "npm nao encontrado"

  rm -rf "$fake_bin"
}
