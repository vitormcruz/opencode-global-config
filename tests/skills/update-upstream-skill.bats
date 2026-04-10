#!/usr/bin/env bats
# tests/skills/update-upstream-skill.bats — testa scripts/skills/update-upstream-skill

load "../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/skills/update-upstream-skill"

# ---------------------------------------------------------------------------
# Ajuda e opções
# ---------------------------------------------------------------------------

@test "update-upstream-skill --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
}

@test "update-upstream-skill --help exibe texto de uso" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "update-upstream-skill"
}

@test "update-upstream-skill sem argumento retorna exit 2" {
  run bash "$SCRIPT"
  assert_failure
  [ "$status" -eq 2 ]
}

# ---------------------------------------------------------------------------
# Skill inexistente → status: no-clear-update-flow (sem UPSTREAM.md)
# ---------------------------------------------------------------------------

@test "update-upstream-skill com skill inexistente retorna exit 0" {
  run bash "$SCRIPT" skill-que-nao-existe-xyz
  assert_success
}

@test "update-upstream-skill com skill inexistente reporta status no-clear-update-flow" {
  run bash "$SCRIPT" skill-que-nao-existe-xyz
  assert_success
  assert_output --partial "status: no-clear-update-flow"
}

@test "update-upstream-skill com skill inexistente informa nome da skill" {
  run bash "$SCRIPT" skill-que-nao-existe-xyz
  assert_success
  assert_output --partial "skill: skill-que-nao-existe-xyz"
}

# ---------------------------------------------------------------------------
# Skill válida com UPSTREAM.md (prompt-improver)
# ---------------------------------------------------------------------------

@test "update-upstream-skill com prompt-improver reporta skill no output" {
  run bash "$SCRIPT" prompt-improver
  assert_success
  assert_output --partial "skill: prompt-improver"
}

@test "update-upstream-skill com prompt-improver reporta status válido" {
  run bash "$SCRIPT" prompt-improver
  assert_success
  # Status deve ser um dos valores documentados
  assert_output --partial "status:"
}

# ---------------------------------------------------------------------------
# Skill sem UPSTREAM.md (ex: doc-extract)
# ---------------------------------------------------------------------------

@test "update-upstream-skill com skill sem UPSTREAM.md reporta no-clear-update-flow" {
  run bash "$SCRIPT" doc-extract
  assert_success
  assert_output --partial "status: no-clear-update-flow"
}
