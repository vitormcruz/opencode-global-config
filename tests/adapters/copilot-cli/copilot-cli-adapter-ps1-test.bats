#!/usr/bin/env bats

load "../../helpers/test_helper"

setup() {
  common_setup
}

teardown() {
  common_teardown
}

SCRIPT="$REPO_ROOT/adapters/copilot-cli/copilot-cli-adapter.ps1"

@test "adapter PowerShell define conversão de frontmatter" {
  run grep -q 'function Convert-AgentFrontmatter' "$SCRIPT"
  assert_success
  run grep -q "user-invocable: false" "$SCRIPT"
  assert_success
  run grep -q 'tools.Add' "$SCRIPT"
  assert_success
}

@test "adapter PowerShell usa destinos nativos Copilot CLI" {
  run grep -q 'AgentsDir.*\.copilot\\agents' "$SCRIPT"
  assert_success
  run grep -q 'function Sync-CommandsAsSkills' "$SCRIPT"
  assert_success
  run grep -q '^function Sync-Mcp[[:space:]]*{' "$SCRIPT"
  assert_failure
  run grep -qi 'vscode\|Code\\User\|McpJson' "$SCRIPT"
  assert_failure
}

@test "adapter PowerShell valida frontmatter de skills" {
  run grep -q 'function Adapt-SkillForCopilot' "$SCRIPT"
  assert_success
  run grep -q 'SkillName.*64' "$SCRIPT"
  assert_success
  run grep -q 'name: \$SkillName' "$SCRIPT"
  assert_success
}
