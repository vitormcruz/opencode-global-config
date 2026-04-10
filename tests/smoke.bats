#!/usr/bin/env bats
# tests/smoke.bats — smoke test E2E da Camada 1
# Valida o estado completo do sistema após bootstrap

load "helpers/test_helper"

setup()    { common_setup; }
teardown() { common_teardown; }

# ---------------------------------------------------------------------------
# Bootstrap completo
# ---------------------------------------------------------------------------

@test "smoke: opencode-link --yes executa com sucesso" {
  run bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_success
}

# ---------------------------------------------------------------------------
# Diretório e symlinks
# ---------------------------------------------------------------------------

@test "smoke: ~/.config/opencode existe após bootstrap" {
  bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_dir_exist "$TEST_CONFIG_DIR"
}

@test "smoke: symlink agents/ aponta para repo" {
  bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_symlink_to "$REPO_ROOT/agents" "$TEST_CONFIG_DIR/agents"
}

@test "smoke: symlink commands/ aponta para repo" {
  bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_symlink_to "$REPO_ROOT/commands" "$TEST_CONFIG_DIR/commands"
}

@test "smoke: symlink opencode.json aponta para repo" {
  bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_symlink_to "$REPO_ROOT/opencode.json" "$TEST_CONFIG_DIR/opencode.json"
}

@test "smoke: symlink skills/ aponta para repo" {
  bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_symlink_to "$REPO_ROOT/skills" "$TEST_CONFIG_DIR/skills"
}

@test "smoke: symlink scripts/ aponta para repo" {
  bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_symlink_to "$REPO_ROOT/scripts" "$TEST_CONFIG_DIR/scripts"
}

# ---------------------------------------------------------------------------
# AGENTS.md NÃO deve existir como symlink global
# ---------------------------------------------------------------------------

@test "smoke: ~/.config/opencode/AGENTS.md não existe" {
  bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_not_exist "$TEST_CONFIG_DIR/AGENTS.md"
}

# ---------------------------------------------------------------------------
# .bashrc
# ---------------------------------------------------------------------------

@test "smoke: .bashrc contém OPENCODE_ENABLE_EXA=1" {
  bash "$REPO_ROOT/scripts/opencode-link" --yes
  run grep "OPENCODE_ENABLE_EXA=1" "$TEST_BASHRC"
  assert_success
}

# ---------------------------------------------------------------------------
# opencode.json acessível via symlink e válido
# ---------------------------------------------------------------------------

@test "smoke: opencode.json é legível via symlink" {
  bash "$REPO_ROOT/scripts/opencode-link" --yes
  assert_file_exist "$TEST_CONFIG_DIR/opencode.json"
}

@test "smoke: opencode.json é JSON válido (JSONC via node)" {
  bash "$REPO_ROOT/scripts/opencode-link" --yes
  run node -e "
const fs = require('fs');
const src = fs.readFileSync('$TEST_CONFIG_DIR/opencode.json', 'utf8');
let result = '';
let inStr = false;
let i = 0;
while (i < src.length) {
  if (!inStr && src[i] === '\"') { inStr = true; result += src[i++]; continue; }
  if (inStr && src[i] === '\\\\\\\\') { result += src[i] + src[i+1]; i+=2; continue; }
  if (inStr && src[i] === '\"') { inStr = false; result += src[i++]; continue; }
  if (!inStr && src[i] === '/' && src[i+1] === '/') {
    while (i < src.length && src[i] !== '\n') i++;
    continue;
  }
  result += src[i++];
}
JSON.parse(result);
console.log('valid');
"
  assert_success
  assert_output "valid"
}

# ---------------------------------------------------------------------------
# Skills acessíveis via symlink
# ---------------------------------------------------------------------------

@test "smoke: skills/ acessível via symlink contém ao menos uma skill" {
  bash "$REPO_ROOT/scripts/opencode-link" --yes
  local skills_dir="$TEST_CONFIG_DIR/skills"
  run bash -c "ls '$skills_dir' | head -1"
  assert_success
  [ -n "$output" ]
}

@test "smoke: cada skill acessível tem SKILL.md" {
  bash "$REPO_ROOT/scripts/opencode-link" --yes
  local skills_dir="$TEST_CONFIG_DIR/skills"
  local failed=0
  for skill_dir in "$skills_dir"/*/; do
    if [[ ! -f "$skill_dir/SKILL.md" ]]; then
      echo "SKILL.md ausente em: $skill_dir"
      failed=1
    fi
  done
  [ "$failed" -eq 0 ]
}
