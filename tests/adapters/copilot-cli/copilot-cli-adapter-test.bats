#!/usr/bin/env bats

load "../../helpers/test_helper"

setup() {
  common_setup
  DEST_ROOT="$TEST_HOME/copilot-dest"
  export DEST_ROOT
}

teardown() {
  common_teardown
}

run_adapter() {
  run env DestRoot="$DEST_ROOT" "$REPO_ROOT/adapters/copilot-cli/copilot-cli-adapter.sh" --yes --quiet
}

@test "adapter Copilot converte frontmatter e tools do agente" {
  run_adapter
  assert_success
  assert_file_exist "$DEST_ROOT/.copilot/agents/eng-software.agent.md"
  run grep -q '^tools: \["read", "edit", "execute", "search"\]$' \
    "$DEST_ROOT/.copilot/agents/eng-software.agent.md"
  assert_success
  run grep -q '^temperature:' "$DEST_ROOT/.copilot/agents/eng-software.agent.md"
  assert_failure
}

@test "adapter Copilot marca subagente como não invocável" {
  run_adapter
  assert_success
  run grep -q '^user-invocable: false$' \
    "$DEST_ROOT/.copilot/agents/revisor-historia.agent.md"
  assert_success
}

@test "adapter Copilot converte os três commands em skills" {
  run_adapter
  assert_success
  for skill in index-codebase bench-indexing sync-upstream-skills; do
    assert_file_exist "$DEST_ROOT/.copilot/skills/$skill/SKILL.md"
    run grep -q "^name: $skill$" "$DEST_ROOT/.copilot/skills/$skill/SKILL.md"
    assert_success
  done
}

@test "adapter Copilot adiciona frontmatter à skill sem frontmatter" {
  run_adapter
  assert_success
  run grep -q '^name: browser-testing$' \
    "$DEST_ROOT/.copilot/skills/browser-testing/SKILL.md"
  assert_success
  run grep -q '^description:' "$DEST_ROOT/.copilot/skills/browser-testing/SKILL.md"
  assert_success
}

@test "adapter Copilot copia default-artifacts e não cria destinos legados" {
  run_adapter
  assert_success
  assert_file_exist "$DEST_ROOT/.copilot/agents/default-artifacts/doc-readme.md"
  assert_file_exist "$DEST_ROOT/.copilot/agents/default-artifacts/harness-section.md"
  assert_not_exist "$DEST_ROOT/.vscode-server"
  assert_not_exist "$DEST_ROOT/.copilot/agents/eng-software.md"
  assert_not_exist "$DEST_ROOT/.copilot/commands"
}
