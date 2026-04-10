#!/usr/bin/env bash
# tests/helpers/test_helper.bash — setup/teardown compartilhado

# Carrega libs BATS
BATS_LIBS_DIR="$(dirname "${BASH_SOURCE[0]}")/../bats-libs"

load "$BATS_LIBS_DIR/bats-support/load.bash"
load "$BATS_LIBS_DIR/bats-assert/load.bash"
load "$BATS_LIBS_DIR/bats-file/load.bash"

# Raiz do repositório
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Diretório temporário para sandbox de HOME
common_setup() {
  TEST_HOME="$(mktemp -d)"
  TEST_CONFIG_DIR="$TEST_HOME/.config/opencode"
  TEST_BASHRC="$TEST_HOME/.bashrc"
  touch "$TEST_BASHRC"
  export HOME="$TEST_HOME"
  export XDG_CONFIG_HOME="$TEST_HOME/.config"
}

common_teardown() {
  if [[ -n "$TEST_HOME" && "$TEST_HOME" == /tmp/* ]]; then
    rm -rf "$TEST_HOME"
  fi
}
