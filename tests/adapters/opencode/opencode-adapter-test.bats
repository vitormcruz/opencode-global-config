#!/usr/bin/env bats

load "../../helpers/test_helper"

setup() {
  common_setup
}

teardown() {
  common_teardown
}

@test "adapter OpenCode cria links para a fonte canônica" {
  run bash "$REPO_ROOT/adapters/opencode/opencode-adapter.sh" --yes
  assert_success
  assert_symlink_to "$REPO_ROOT/agents" "$TEST_CONFIG_DIR/agents"
  assert_symlink_to "$REPO_ROOT/commands" "$TEST_CONFIG_DIR/commands"
  assert_symlink_to "$REPO_ROOT/skills" "$TEST_CONFIG_DIR/skills"
  assert_symlink_to "$REPO_ROOT/opencode.json" "$TEST_CONFIG_DIR/opencode.json"
}

@test "adapter OpenCode não cria link para AGENTS.md" {
  run bash "$REPO_ROOT/adapters/opencode/opencode-adapter.sh" --yes
  assert_success
  assert_not_exist "$TEST_CONFIG_DIR/AGENTS.md"
}

@test "adapter OpenCode é idempotente" {
  run bash "$REPO_ROOT/adapters/opencode/opencode-adapter.sh" --yes
  assert_success
  run bash "$REPO_ROOT/adapters/opencode/opencode-adapter.sh" --yes
  assert_success
  assert_symlink_to "$REPO_ROOT/skills" "$TEST_CONFIG_DIR/skills"
}
