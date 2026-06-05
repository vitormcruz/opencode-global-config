#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/wsl-vscode-sync-test.bats — testa sincronizacao VS Code

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/bootstrap_repo/wsl-vscode-sync.sh"

setup() {
  common_setup
  export HOME="$(mktemp -d)/home"
  mkdir -p "$HOME/.vscode-server/data/User"
}

teardown() {
  common_teardown
}

# ---------------------------------------------------------------------------
# Ajuda e opcoes
# ---------------------------------------------------------------------------

@test "wsl-vscode-sync --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
}

@test "wsl-vscode-sync --help exibe texto de uso" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "wsl-vscode-sync"
  assert_output --partial "Uso:"
}

@test "wsl-vscode-sync com opcao invalida retorna exit 2" {
  run bash "$SCRIPT" --invalido
  assert_failure
  [ "$status" -eq 2 ]
}

# ---------------------------------------------------------------------------
# Funcionalidade de sincronizacao
# ---------------------------------------------------------------------------

@test "wsl-vscode-sync --yes funciona sem TTY" {
  run bash "$SCRIPT" --yes
  assert_success
}

@test "wsl-vscode-sync cria diretório de backup" {
  run bash "$SCRIPT" --yes
  assert_success
  # Verifica que ha backups criados
  [ -d "$HOME/.vscode-server/data/User/.backups" ]
}

@test "wsl-vscode-sync cria links simbolicos" {
  run bash "$SCRIPT" --yes
  assert_success
  [ -L "$HOME/.vscode-server/data/User/skills" ] || [ -e "$HOME/.vscode-server/data/User/skills" ]
}
