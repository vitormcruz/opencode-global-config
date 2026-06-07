#!/usr/bin/env bats
# tests/skills/code-explorer-priority-test.bats — valida skill code-explorer-priority

load "../../helpers/test_helper"

@test "code-explorer-priority/SKILL.md existe" {
  assert_file_exist "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
}

@test "code-explorer-priority SKILL.md tem frontmatter com name" {
  run grep "^name:" "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
  assert_success
  assert_output --partial "code-explorer-priority"
}

@test "code-explorer-priority SKILL.md tem frontmatter com description" {
  run grep "^description:" "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
  assert_success
}

@test "code-explorer-priority SKILL.md menciona codebase-memory na description" {
  run grep "^description:" "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
  assert_success
  assert_output --partial "codebase-memory"
}

@test "code-explorer-priority SKILL.md menciona doctree na description" {
  run grep "^description:" "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
  assert_success
  assert_output --partial "doctree"
}

@test "code-explorer-priority SKILL.md tem secao Acesso por Cliente" {
  run grep -c "Acesso por Cliente" "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "code-explorer-priority SKILL.md tem secao OpenCode" {
  run grep -c "OpenCode" "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "code-explorer-priority SKILL.md tem secao GitHub Copilot" {
  run grep -c "GitHub Copilot" "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "code-explorer-priority SKILL.md tem secao Passo 0: Confirmar projeto indexado" {
  run grep -c "Passo 0" "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "code-explorer-priority SKILL.md tem secao Passo 1: Classificar" {
  run grep -c "Passo 1" "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "code-explorer-priority SKILL.md tem secao Passo 2: Executar com recovery" {
  run grep -c "Passo 2" "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "code-explorer-priority SKILL.md tem secao Passo 3: Navegar resultados" {
  run grep -c "Passo 3" "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "code-explorer-priority SKILL.md menciona mcp codebase-memory (CLI Copilot)" {
  run grep -c "mcp codebase-memory" "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "code-explorer-priority SKILL.md menciona mcp doctree (CLI Copilot)" {
  run grep -c "mcp doctree" "$REPO_ROOT/skills/code-explorer-priority/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}
