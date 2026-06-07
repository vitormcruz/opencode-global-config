#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/wsl-copilot-sync-test.bats — testa sincronizacao Copilot

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/bootstrap_repo/wsl-copilot-sync.sh"

setup() {
  common_setup
  export HOME="$(mktemp -d)/home"
  mkdir -p "$HOME/.copilot"
}

teardown() {
  common_teardown
}

# ---------------------------------------------------------------------------
# Ajuda e opcoes
# ---------------------------------------------------------------------------

@test "wsl-copilot-sync --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
}

@test "wsl-copilot-sync --help exibe texto de uso" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "wsl-copilot-sync"
  assert_output --partial "Uso:"
}

@test "wsl-copilot-sync com opcao invalida retorna exit 2" {
  run bash "$SCRIPT" --invalido
  assert_failure
  [ "$status" -eq 2 ]
}

# ---------------------------------------------------------------------------
# Funcionalidade de sincronizacao
# ---------------------------------------------------------------------------

@test "wsl-copilot-sync --yes funciona sem TTY" {
  run bash "$SCRIPT" --yes
  assert_success
}

@test "wsl-copilot-sync cria diretório de backup" {
  run bash "$SCRIPT" --yes
  assert_success
  # Verifica que ha backups criados
  [ -d "$HOME/.copilot/.backups" ]
}

@test "wsl-copilot-sync cria links simbolicos" {
  run bash "$SCRIPT" --yes
  assert_success
  [ -L "$HOME/.copilot/skills" ] || [ -e "$HOME/.copilot/skills" ]
}
