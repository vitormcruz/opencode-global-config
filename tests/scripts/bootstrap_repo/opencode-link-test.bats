#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/opencode-link-test.bats — testa o script de bootstrap

load "../../helpers/test_helper"

setup() {
  common_setup
  export OPENCODE_SKIP_DEPS=1
  export OPENCODE_SKIP_SKILL_SYNC=1
}

teardown() {
  common_teardown
}

# ---------------------------------------------------------------------------
# Ajuda e opções
# ---------------------------------------------------------------------------

@test "opencode-link --help retorna exit 0" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --help
  assert_success
}

@test "opencode-link --help exibe texto de uso" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --help
  assert_success
  assert_output --partial "opencode-link"
}

@test "opencode-link com opção inválida retorna exit 2" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --opcao-inexistente
  assert_failure
  [ "$status" -eq 2 ]
}

# ---------------------------------------------------------------------------
# Execução básica com --yes
# ---------------------------------------------------------------------------

@test "opencode-link --yes cria diretório ~/.config/opencode" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
  assert_dir_exist "$TEST_CONFIG_DIR"
}

@test "opencode-link --yes funciona sem TTY (pipe)" {
  run bash -c "echo '' | bash '$REPO_ROOT/scripts/bootstrap_repo/opencode-link' --yes"
  assert_success
}

# ---------------------------------------------------------------------------
# Symlinks — os 5 links esperados
# ---------------------------------------------------------------------------

@test "opencode-link cria symlink para agents/" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
  assert_symlink_to "$REPO_ROOT/agents" "$TEST_CONFIG_DIR/agents"
}

@test "opencode-link cria symlink para commands/" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
  assert_symlink_to "$REPO_ROOT/commands" "$TEST_CONFIG_DIR/commands"
}

@test "opencode-link cria symlink para opencode.json" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
  assert_symlink_to "$REPO_ROOT/opencode.json" "$TEST_CONFIG_DIR/opencode.json"
}

@test "opencode-link cria symlink para skills/" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
  assert_symlink_to "$REPO_ROOT/skills" "$TEST_CONFIG_DIR/skills"
}

@test "opencode-link cria symlink para scripts/" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
  assert_symlink_to "$REPO_ROOT/scripts" "$TEST_CONFIG_DIR/scripts"
}

# ---------------------------------------------------------------------------
# AGENTS.md NÃO deve ser linkado globalmente (decisão #10 do plano)
# ---------------------------------------------------------------------------

@test "opencode-link NÃO cria symlink para AGENTS.md" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
  assert_not_exist "$TEST_CONFIG_DIR/AGENTS.md"
}

# ---------------------------------------------------------------------------
# .bashrc
# ---------------------------------------------------------------------------

@test "opencode-link adiciona OPENCODE_ENABLE_EXA=1 ao .bashrc" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
  run grep "OPENCODE_ENABLE_EXA=1" "$TEST_BASHRC"
  assert_success
}

@test "opencode-link adiciona BATS_LIB_PATH ao .bashrc" {
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
  run grep 'BATS_LIB_PATH="$HOME/.local/lib/bats"' "$TEST_BASHRC"
  assert_success
}

@test "opencode-link não duplica OPENCODE_ENABLE_EXA=1 ao rodar 2x" {
  bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  run grep -c "OPENCODE_ENABLE_EXA=1" "$TEST_BASHRC"
  assert_success
  [ "$output" -eq 1 ]
}

@test "opencode-link não duplica BATS_LIB_PATH ao rodar 2x" {
  bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  run grep -c 'BATS_LIB_PATH="$HOME/.local/lib/bats"' "$TEST_BASHRC"
  assert_success
  [ "$output" -eq 1 ]
}

# ---------------------------------------------------------------------------
# Idempotência
# ---------------------------------------------------------------------------

@test "opencode-link é idempotente (2ª execução retorna success)" {
  bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success
}

@test "opencode-link é idempotente (symlinks permanecem corretos após 2ª execução)" {
  bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_symlink_to "$REPO_ROOT/agents"       "$TEST_CONFIG_DIR/agents"
  assert_symlink_to "$REPO_ROOT/commands"     "$TEST_CONFIG_DIR/commands"
  assert_symlink_to "$REPO_ROOT/opencode.json" "$TEST_CONFIG_DIR/opencode.json"
  assert_symlink_to "$REPO_ROOT/skills"       "$TEST_CONFIG_DIR/skills"
  assert_symlink_to "$REPO_ROOT/scripts"      "$TEST_CONFIG_DIR/scripts"
}

# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

@test "opencode-link faz backup de arquivo preexistente no destino" {
  mkdir -p "$TEST_CONFIG_DIR"
  echo "config antiga" > "$TEST_CONFIG_DIR/opencode.json"

  run bash "$REPO_ROOT/scripts/bootstrap_repo/opencode-link" --yes
  assert_success

  # O link deve existir e apontar para o repo
  assert_symlink_to "$REPO_ROOT/opencode.json" "$TEST_CONFIG_DIR/opencode.json"

  # O backup deve ter sido criado
  local backup_count
  backup_count=$(find "$TEST_HOME/.config/opencode-backup" -name "opencode.json*" 2>/dev/null | wc -l)
  [ "$backup_count" -ge 1 ]
}
