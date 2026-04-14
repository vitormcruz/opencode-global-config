#!/usr/bin/env bats
# tests/scripts/skills/addyosmani-sync-test.bats — testa scripts/addyosmani/sync

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/addyosmani/sync"

# ---------------------------------------------------------------------------
# Ajuda e opções
# ---------------------------------------------------------------------------

@test "addyosmani/sync existe e é executável" {
  assert_file_executable "$SCRIPT"
}

@test "addyosmani/sync --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
}

@test "addyosmani/sync --help exibe texto de uso" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "sync"
  assert_output --partial "addyosmani"
}

@test "addyosmani/sync opção inválida retorna exit 2" {
  run bash "$SCRIPT" --opcao-invalida
  assert_failure
  [ "$status" -eq 2 ]
}

# ---------------------------------------------------------------------------
# check-only — sem rede, apenas valida que o script sai sem modificar nada
# ---------------------------------------------------------------------------

@test "addyosmani/sync --check-only requer git disponível" {
  command -v git >/dev/null 2>&1 || skip "git não disponível"
  # check-only tenta clonar; esperamos falha de rede ou sucesso —
  # o importante é que exit code seja 0 ou 1 (não 2 = argumento inválido)
  run timeout 30 bash "$SCRIPT" --check-only 2>/dev/null || true
  [ "$status" -ne 2 ]
}

# ---------------------------------------------------------------------------
# Validação estática — 12 skills devem ter SKILL.md e UPSTREAM.md
# ---------------------------------------------------------------------------

@test "12 skills addyosmani têm SKILL.md" {
  local skills=(
    test-driven-development
    code-review-and-quality
    code-simplification
    security-and-hardening
    documentation-and-adrs
    debugging-and-error-recovery
    git-workflow-and-versioning
    spec-driven-development
    planning-and-task-breakdown
    api-and-interface-design
    performance-optimization
    frontend-ui-engineering
  )
  local failed=0
  for s in "${skills[@]}"; do
    if [[ ! -f "$REPO_ROOT/skills/$s/SKILL.md" ]]; then
      echo "SKILL.md ausente: $s"
      failed=1
    fi
  done
  [[ $failed -eq 0 ]]
}

@test "12 skills addyosmani têm UPSTREAM.md" {
  local skills=(
    test-driven-development
    code-review-and-quality
    code-simplification
    security-and-hardening
    documentation-and-adrs
    debugging-and-error-recovery
    git-workflow-and-versioning
    spec-driven-development
    planning-and-task-breakdown
    api-and-interface-design
    performance-optimization
    frontend-ui-engineering
  )
  local failed=0
  for s in "${skills[@]}"; do
    if [[ ! -f "$REPO_ROOT/skills/$s/UPSTREAM.md" ]]; then
      echo "UPSTREAM.md ausente: $s"
      failed=1
    fi
  done
  [[ $failed -eq 0 ]]
}

@test "UPSTREAM.md das skills addyosmani referencia o repo correto" {
  run grep -l "addyosmani/agent-skills" \
    "$REPO_ROOT/skills/test-driven-development/UPSTREAM.md" \
    "$REPO_ROOT/skills/security-and-hardening/UPSTREAM.md"
  assert_success
}

@test "skills addyosmani com references têm arquivos esperados" {
  assert_file_exist "$REPO_ROOT/skills/test-driven-development/references/testing-patterns.md"
  assert_file_exist "$REPO_ROOT/skills/security-and-hardening/references/security-checklist.md"
  assert_file_exist "$REPO_ROOT/skills/performance-optimization/references/performance-checklist.md"
  assert_file_exist "$REPO_ROOT/skills/frontend-ui-engineering/references/accessibility-checklist.md"
}
