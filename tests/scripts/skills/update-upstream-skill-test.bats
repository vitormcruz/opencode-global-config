#!/usr/bin/env bats
# tests/scripts/skills/update-upstream-skill-test.bats — testa scripts/skills/update-upstream-skill.sh

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/skills/update-upstream-skill.sh"

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
# Skill válida com UPSTREAM.md (prompt-improver) - modo --dry-run
# ---------------------------------------------------------------------------

@test "update-upstream-skill com prompt-improver reporta skill no output" {
  run bash "$SCRIPT" --dry-run prompt-improver
  assert_success
  assert_output --partial "skill: prompt-improver"
}

@test "update-upstream-skill com prompt-improver reporta status dry-run" {
  run bash "$SCRIPT" --dry-run prompt-improver
  assert_success
  # Status deve ser dry-run em modo nao-destrutivo
  assert_output --partial "status: dry-run"
}

@test "update-upstream-skill com prompt-improver --dry-run nao modifica arquivos" {
  # Salva hash do UPSTREAM.md antes
  local before_hash
  before_hash=$(md5sum "$REPO_ROOT/skills/prompt-improver/UPSTREAM.md" | awk '{print $1}')
  
  run bash "$SCRIPT" --dry-run prompt-improver
  assert_success
  
  # Verifica que o arquivo nao mudou
  local after_hash
  after_hash=$(md5sum "$REPO_ROOT/skills/prompt-improver/UPSTREAM.md" | awk '{print $1}')
  [ "$before_hash" = "$after_hash" ]
}

# ---------------------------------------------------------------------------
# Skill sem UPSTREAM.md (ex: doc-extract)
# ---------------------------------------------------------------------------

@test "update-upstream-skill com skill sem UPSTREAM.md reporta no-clear-update-flow" {
  run bash "$SCRIPT" doc-extract
  assert_success
  assert_output --partial "status: no-clear-update-flow"
}
