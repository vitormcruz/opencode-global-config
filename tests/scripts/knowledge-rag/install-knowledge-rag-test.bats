#!/usr/bin/env bats
# tests/scripts/knowledge-rag/install-knowledge-rag-test.bats
# Testa o script scripts/knowledge-rag/install.sh

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/knowledge-rag/install.sh"

setup()    { common_setup; }
teardown() { common_teardown; }

@test "knowledge-rag/install --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "knowledge-rag/install"
  assert_output --partial "Uso:"
}

@test "knowledge-rag/install com opcao invalida retorna exit 2" {
  run bash "$SCRIPT" --opcao-inexistente
  assert_failure
  [ "$status" -eq 2 ]
}

@test "knowledge-rag/install --check-only reporta OK quando knowledge-rag disponivel" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  # Criar fake knowledge-rag
  printf '#!/bin/sh\necho "knowledge-rag 1.0.0"\n' > "$fake_bin/knowledge-rag"
  chmod +x "$fake_bin/knowledge-rag"

  # Criar fake python3 >= 3.10
  printf '#!/bin/sh\necho "Python 3.10.0"\n' > "$fake_bin/python3"
  chmod +x "$fake_bin/python3"

  run env PATH="$fake_bin:/usr/bin:/bin" /usr/bin/bash "$SCRIPT" --check-only
  assert_success
  assert_output --partial "knowledge-rag"

  rm -rf "$fake_bin"
}

@test "knowledge-rag/install --check-only reporta missing quando python3 < 3.10" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  # Criar fake python3 < 3.10
  printf '#!/bin/sh\necho "Python 3.9.0"\n' > "$fake_bin/python3"
  chmod +x "$fake_bin/python3"

  run env PATH="$fake_bin:/usr/bin:/bin" /usr/bin/bash "$SCRIPT" --check-only
  assert_failure
  assert_output --partial "Python 3.10+"

  rm -rf "$fake_bin"
}

@test "knowledge-rag/install --check-only reporta missing quando python3 ausente" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --check-only
  assert_failure
  assert_output --partial "Python 3.10+"

  rm -rf "$fake_bin"
}
