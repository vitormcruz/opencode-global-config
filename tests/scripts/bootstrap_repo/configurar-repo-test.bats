#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/configurar-repo-test.bats — testa o script principal

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/bootstrap_repo/configurar-repo.sh"

setup() {
  common_setup
  export HOME="$(mktemp -d)/home"
  mkdir -p "$HOME"
}

teardown() {
  common_teardown
}

# ---------------------------------------------------------------------------
# Ajuda e opcoes
# ---------------------------------------------------------------------------

@test "configurar-repo --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
}

@test "configurar-repo --help exibe texto de uso" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "configurar-repo"
  assert_output --partial "Uso:"
  assert_output --partial "wsl-install-deps"
  assert_output --partial "wsl-vscode-sync"
  assert_output --partial "opencode-link"
}

@test "configurar-repo com opcao invalida retorna exit 2" {
  run bash "$SCRIPT" --invalido" 
  assert_failure
  [ "$status" -eq 2 ]
}

@test "configurar-repo retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
}

# ---------------------------------------------------------------------------
# Variaveis de ambiente SKIP
# ---------------------------------------------------------------------------

@test "configurar-repo respeita OPENCODE_SKIP_DEPS=1" {
  # Quando pula deps, ainda tenta rodar as outras partes
  export OPENCODE_SKIP_DEPS=1
  export OPENCODE_SKIP_VSCODE_SYNC=1
  export OPENCODE_SKIP_LINKS=1

  run bash "$SCRIPT" --quiet
  assert_success
}

@test "configurar-repo respeita OPENCODE_SKIP_VSCODE_SYNC=1" {
  export OPENCODE_SKIP_VSCODE_SYNC=1
  export OPENCODE_SKIP_LINKS=1

  run bash "$SCRIPT" --quiet
  assert_success
}

@test "configurar-repo respeita OPENCODE_SKIP_LINKS=1" {
  export OPENCODE_SKIP_LINKS=1

  run bash "$SCRIPT" --quiet
  assert_success
}
