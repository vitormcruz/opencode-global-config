#!/usr/bin/env bats
# tests/skills/list-updatable.bats — testa scripts/skills/list-updatable

load "../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/skills/list-updatable"

# ---------------------------------------------------------------------------
# Ajuda e opções
# ---------------------------------------------------------------------------

@test "list-updatable --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
}

@test "list-updatable --help exibe texto de uso" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "list-updatable"
}

@test "list-updatable opção inválida retorna exit 2" {
  run bash "$SCRIPT" --opcao-inexistente
  assert_failure
  [ "$status" -eq 2 ]
}

# ---------------------------------------------------------------------------
# Saída coerente com skills que têm UPSTREAM.md
# ---------------------------------------------------------------------------

@test "list-updatable lista prompt-improver (tem UPSTREAM.md)" {
  run bash "$SCRIPT"
  assert_success
  assert_output --partial "prompt-improver"
}

@test "list-updatable não lista skills sem UPSTREAM.md" {
  run bash "$SCRIPT"
  assert_success
  # doc-extract não tem UPSTREAM.md → não deve aparecer
  refute_output --partial "doc-extract"
  # md-export não tem UPSTREAM.md
  refute_output --partial "md-export"
}

@test "list-updatable saída coincide com skills que têm UPSTREAM.md no repo" {
  # Conta skills com UPSTREAM.md
  local expected_count
  expected_count=$(find "$REPO_ROOT/skills" -name "UPSTREAM.md" -maxdepth 2 | wc -l | tr -d ' ')

  run bash "$SCRIPT"
  assert_success

  local actual_count
  actual_count=$(echo "$output" | grep -c . || echo 0)

  [ "$actual_count" -eq "$expected_count" ]
}

@test "list-updatable saída está em ordem alfabética" {
  run bash "$SCRIPT"
  assert_success

  if [ -z "$output" ]; then
    skip "nenhuma skill atualizável encontrada"
  fi

  local sorted
  sorted=$(echo "$output" | LC_ALL=C sort)
  [ "$output" = "$sorted" ]
}
