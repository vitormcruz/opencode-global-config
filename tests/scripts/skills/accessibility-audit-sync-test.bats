#!/usr/bin/env bats
# tests/scripts/skills/accessibility-audit-sync-test.bats
# testa scripts/accessibility-audit/sync

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/accessibility-audit/sync"

# ---------------------------------------------------------------------------
# Ajuda e opções
# ---------------------------------------------------------------------------

@test "accessibility-audit/sync existe e é executável" {
  assert_file_executable "$SCRIPT"
}

@test "accessibility-audit/sync --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
}

@test "accessibility-audit/sync --help exibe texto de uso" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "accessibility"
}

@test "accessibility-audit/sync opção inválida retorna exit 2" {
  run bash "$SCRIPT" --opcao-invalida
  assert_failure
  [ "$status" -eq 2 ]
}

# ---------------------------------------------------------------------------
# check-only — não modifica nada, apenas valida args
# ---------------------------------------------------------------------------

@test "accessibility-audit/sync --check-only não retorna exit 2" {
  command -v git >/dev/null 2>&1 || skip "git não disponível"
  run timeout 30 bash "$SCRIPT" --check-only 2>/dev/null || true
  [ "$status" -ne 2 ]
}

# ---------------------------------------------------------------------------
# Validação estática — skill deve ter SKILL.md, UPSTREAM.md e resources
# ---------------------------------------------------------------------------

@test "skills/accessibility-audit/SKILL.md existe" {
  assert_file_exist "$REPO_ROOT/skills/accessibility-audit/SKILL.md"
}

@test "skills/accessibility-audit/UPSTREAM.md existe" {
  assert_file_exist "$REPO_ROOT/skills/accessibility-audit/UPSTREAM.md"
}

@test "skills/accessibility-audit/resources/implementation-playbook.md existe" {
  assert_file_exist "$REPO_ROOT/skills/accessibility-audit/resources/implementation-playbook.md"
}

@test "UPSTREAM.md referencia sickn33/antigravity-awesome-skills" {
  run grep -q "sickn33/antigravity-awesome-skills" \
    "$REPO_ROOT/skills/accessibility-audit/UPSTREAM.md"
  assert_success
}

@test "UPSTREAM.md documenta licença MIT + CC BY 4.0" {
  run grep -q "CC BY" "$REPO_ROOT/skills/accessibility-audit/UPSTREAM.md"
  assert_success
}

@test "SKILL.md da accessibility-audit contém triggers PT-BR" {
  run grep -q "acessibilidade\|WCAG\|a11y" \
    "$REPO_ROOT/skills/accessibility-audit/SKILL.md"
  assert_success
}
