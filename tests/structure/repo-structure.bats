#!/usr/bin/env bats
# tests/structure/repo-structure.bats — valida estrutura estática do repo

load "../helpers/test_helper"

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

@test "scripts/opencode-link é executável" {
  assert_file_executable "$REPO_ROOT/scripts/opencode-link"
}

@test "scripts/opencode-install-deps é executável" {
  assert_file_executable "$REPO_ROOT/scripts/opencode-install-deps"
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
