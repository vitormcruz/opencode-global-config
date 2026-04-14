#!/usr/bin/env bats
# tests/structure/repo-structure.bats — valida estrutura estática do repo

load "../../helpers/test_helper"

# ---------------------------------------------------------------------------
# Arquivos obrigatórios do repo
# ---------------------------------------------------------------------------

@test "AGENTS.md existe no repo" {
  assert_file_exist "$REPO_ROOT/AGENTS.md"
}

@test "opencode.json existe no repo" {
  assert_file_exist "$REPO_ROOT/opencode.json"
}

@test "README.md existe no repo" {
  assert_file_exist "$REPO_ROOT/README.md"
}

# ---------------------------------------------------------------------------
# Itens linkados globalmente (apenas estes 5)
# ---------------------------------------------------------------------------

@test "diretório agents/ existe" {
  assert_dir_exist "$REPO_ROOT/agents"
}

@test "diretório commands/ existe" {
  assert_dir_exist "$REPO_ROOT/commands"
}

@test "diretório skills/ existe" {
  assert_dir_exist "$REPO_ROOT/skills"
}

@test "diretório scripts/ existe" {
  assert_dir_exist "$REPO_ROOT/scripts"
}

# ---------------------------------------------------------------------------
# Skills — cada dir em skills/ deve ter SKILL.md
# ---------------------------------------------------------------------------

@test "skills/doc-extract/SKILL.md existe" {
  assert_file_exist "$REPO_ROOT/skills/doc-extract/SKILL.md"
}

@test "skills/md-export/SKILL.md existe" {
  assert_file_exist "$REPO_ROOT/skills/md-export/SKILL.md"
}

@test "skills/svg-to-image/SKILL.md existe" {
  assert_file_exist "$REPO_ROOT/skills/svg-to-image/SKILL.md"
}

@test "skills/prompt-improver/SKILL.md existe" {
  assert_file_exist "$REPO_ROOT/skills/prompt-improver/SKILL.md"
}

@test "skills/web-research-exa-crawl4ai/SKILL.md existe" {
  assert_file_exist "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
}

@test "skills/aws-add-account-sso/SKILL.md existe" {
  assert_file_exist "$REPO_ROOT/skills/aws-add-account-sso/SKILL.md"
}

@test "skills/aws-sso-login/SKILL.md existe" {
  assert_file_exist "$REPO_ROOT/skills/aws-sso-login/SKILL.md"
}

@test "todos os diretórios em skills/ contêm SKILL.md" {
  local failed=0
  for skill_dir in "$REPO_ROOT/skills"/*/; do
    if [[ ! -f "$skill_dir/SKILL.md" ]]; then
      echo "SKILL.md ausente em: $skill_dir"
      failed=1
    fi
  done
  [[ $failed -eq 0 ]]
}

# ---------------------------------------------------------------------------
# Skills addyosmani (12) — SKILL.md + UPSTREAM.md obrigatórios
# ---------------------------------------------------------------------------

@test "skills/test-driven-development tem SKILL.md e UPSTREAM.md" {
  assert_file_exist "$REPO_ROOT/skills/test-driven-development/SKILL.md"
  assert_file_exist "$REPO_ROOT/skills/test-driven-development/UPSTREAM.md"
}

@test "skills/code-review-and-quality tem SKILL.md e UPSTREAM.md" {
  assert_file_exist "$REPO_ROOT/skills/code-review-and-quality/SKILL.md"
  assert_file_exist "$REPO_ROOT/skills/code-review-and-quality/UPSTREAM.md"
}

@test "skills/code-simplification tem SKILL.md e UPSTREAM.md" {
  assert_file_exist "$REPO_ROOT/skills/code-simplification/SKILL.md"
  assert_file_exist "$REPO_ROOT/skills/code-simplification/UPSTREAM.md"
}

@test "skills/security-and-hardening tem SKILL.md e UPSTREAM.md" {
  assert_file_exist "$REPO_ROOT/skills/security-and-hardening/SKILL.md"
  assert_file_exist "$REPO_ROOT/skills/security-and-hardening/UPSTREAM.md"
}

@test "skills/documentation-and-adrs tem SKILL.md e UPSTREAM.md" {
  assert_file_exist "$REPO_ROOT/skills/documentation-and-adrs/SKILL.md"
  assert_file_exist "$REPO_ROOT/skills/documentation-and-adrs/UPSTREAM.md"
}

@test "skills/debugging-and-error-recovery tem SKILL.md e UPSTREAM.md" {
  assert_file_exist "$REPO_ROOT/skills/debugging-and-error-recovery/SKILL.md"
  assert_file_exist "$REPO_ROOT/skills/debugging-and-error-recovery/UPSTREAM.md"
}

@test "skills/git-workflow-and-versioning tem SKILL.md e UPSTREAM.md" {
  assert_file_exist "$REPO_ROOT/skills/git-workflow-and-versioning/SKILL.md"
  assert_file_exist "$REPO_ROOT/skills/git-workflow-and-versioning/UPSTREAM.md"
}

@test "skills/spec-driven-development tem SKILL.md e UPSTREAM.md" {
  assert_file_exist "$REPO_ROOT/skills/spec-driven-development/SKILL.md"
  assert_file_exist "$REPO_ROOT/skills/spec-driven-development/UPSTREAM.md"
}

@test "skills/planning-and-task-breakdown tem SKILL.md e UPSTREAM.md" {
  assert_file_exist "$REPO_ROOT/skills/planning-and-task-breakdown/SKILL.md"
  assert_file_exist "$REPO_ROOT/skills/planning-and-task-breakdown/UPSTREAM.md"
}

@test "skills/api-and-interface-design tem SKILL.md e UPSTREAM.md" {
  assert_file_exist "$REPO_ROOT/skills/api-and-interface-design/SKILL.md"
  assert_file_exist "$REPO_ROOT/skills/api-and-interface-design/UPSTREAM.md"
}

@test "skills/performance-optimization tem SKILL.md e UPSTREAM.md" {
  assert_file_exist "$REPO_ROOT/skills/performance-optimization/SKILL.md"
  assert_file_exist "$REPO_ROOT/skills/performance-optimization/UPSTREAM.md"
}

@test "skills/frontend-ui-engineering tem SKILL.md e UPSTREAM.md" {
  assert_file_exist "$REPO_ROOT/skills/frontend-ui-engineering/SKILL.md"
  assert_file_exist "$REPO_ROOT/skills/frontend-ui-engineering/UPSTREAM.md"
}

# ---------------------------------------------------------------------------
# Skills com references/ obrigatórios
# ---------------------------------------------------------------------------

@test "skills/test-driven-development tem references/testing-patterns.md" {
  assert_file_exist "$REPO_ROOT/skills/test-driven-development/references/testing-patterns.md"
}

@test "skills/security-and-hardening tem references/security-checklist.md" {
  assert_file_exist "$REPO_ROOT/skills/security-and-hardening/references/security-checklist.md"
}

@test "skills/performance-optimization tem references/performance-checklist.md" {
  assert_file_exist "$REPO_ROOT/skills/performance-optimization/references/performance-checklist.md"
}

@test "skills/frontend-ui-engineering tem references/accessibility-checklist.md" {
  assert_file_exist "$REPO_ROOT/skills/frontend-ui-engineering/references/accessibility-checklist.md"
}

# ---------------------------------------------------------------------------
# Skill accessibility-audit (antigravity)
# ---------------------------------------------------------------------------

@test "skills/accessibility-audit tem SKILL.md e UPSTREAM.md" {
  assert_file_exist "$REPO_ROOT/skills/accessibility-audit/SKILL.md"
  assert_file_exist "$REPO_ROOT/skills/accessibility-audit/UPSTREAM.md"
}

@test "skills/accessibility-audit tem resources/implementation-playbook.md" {
  assert_file_exist "$REPO_ROOT/skills/accessibility-audit/resources/implementation-playbook.md"
}

# ---------------------------------------------------------------------------
# Shannon plugin — script e UPSTREAM.md
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Agentes — cada .md em agents/ deve ter frontmatter válido
# ---------------------------------------------------------------------------

@test "agents/analista-bd.md tem frontmatter" {
  run grep -c "^---$" "$REPO_ROOT/agents/analista-bd.md"
  assert_success
  [[ "$output" -ge 2 ]]
}

@test "agents/analista.md tem frontmatter" {
  run grep -c "^---$" "$REPO_ROOT/agents/analista.md"
  assert_success
  [[ "$output" -ge 2 ]]
}

@test "agents/aws-analista.md tem frontmatter" {
  run grep -c "^---$" "$REPO_ROOT/agents/aws-analista.md"
  assert_success
  [[ "$output" -ge 2 ]]
}

@test "agents/revisor-historia.md tem frontmatter" {
  run grep -c "^---$" "$REPO_ROOT/agents/revisor-historia.md"
  assert_success
  [[ "$output" -ge 2 ]]
}

@test "todos os agentes têm campo description no frontmatter" {
  local failed=0
  for agent in "$REPO_ROOT/agents"/*.md; do
    if ! grep -q "^description:" "$agent"; then
      echo "description ausente em: $agent"
      failed=1
    fi
  done
  [[ $failed -eq 0 ]]
}

# ---------------------------------------------------------------------------
# opencode.json — deve ser JSONC válido (sem comentários)
# ---------------------------------------------------------------------------

@test "opencode.json é JSONC válido" {
  run node -e "
const fs = require('fs');
const src = fs.readFileSync('$REPO_ROOT/opencode.json', 'utf8');
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
# Permissões — scripts em scripts/ devem ser executáveis
# ---------------------------------------------------------------------------

@test "scripts/bootstrap_repo/opencode-link é executável" {
  assert_file_executable "$REPO_ROOT/scripts/bootstrap_repo/opencode-link"
}

@test "scripts/bootstrap_repo/opencode-install-deps é executável" {
  assert_file_executable "$REPO_ROOT/scripts/bootstrap_repo/opencode-install-deps"
}

@test "scripts/addyosmani/sync é executável" {
  assert_file_executable "$REPO_ROOT/scripts/addyosmani/sync"
}

@test "scripts/accessibility-audit/sync é executável" {
  assert_file_executable "$REPO_ROOT/scripts/accessibility-audit/sync"
}

@test "scripts/opencode-doc-extract é executável" {
  assert_file_executable "$REPO_ROOT/scripts/opencode-doc-extract"
}

@test "scripts/opencode-md-export é executável" {
  assert_file_executable "$REPO_ROOT/scripts/opencode-md-export"
}

@test "scripts/opencode-svgtoimage é executável" {
  assert_file_executable "$REPO_ROOT/scripts/opencode-svgtoimage"
}
