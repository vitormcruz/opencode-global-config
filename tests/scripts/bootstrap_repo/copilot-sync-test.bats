#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/copilot-sync-test.bats — valida copilot-sync.ps1

load "../../helpers/test_helper"

# ---------------------------------------------------------------------------
# .github/copilot-specific.instructions.md — arquivo versionado e independente
# ---------------------------------------------------------------------------

@test "copilot-sync: .github/copilot-specific.instructions.md existe no repo" {
  assert_file_exist "$REPO_ROOT/.github/copilot-specific.instructions.md"
}

@test "copilot-sync: copilot-specific.instructions.md NAO e copia identica do AGENTS.md" {
  run diff "$REPO_ROOT/.github/copilot-specific.instructions.md" "$REPO_ROOT/AGENTS.md"
  assert_failure
}

@test "copilot-sync: copilot-specific.instructions.md instrui uso do comando mcp" {
  run grep -qE "Use o comando .mcp.|comando \`mcp\`" "$REPO_ROOT/.github/copilot-specific.instructions.md"
  assert_success
}

@test "copilot-sync: copilot-specific.instructions.md contem secao MCP via CLI" {
  run grep -q "MCP via CLI" "$REPO_ROOT/.github/copilot-specific.instructions.md"
  assert_success
}

@test "copilot-sync: copilot-specific.instructions.md referencia servidor crawl4ai" {
  run grep -c "crawl4ai" "$REPO_ROOT/.github/copilot-specific.instructions.md"
  assert_success
  [[ "$output" -ge 2 ]]
}

@test "copilot-sync: copilot-specific.instructions.md menciona que regras gerais estao no AGENTS.md" {
  run grep -q "AGENTS.md" "$REPO_ROOT/.github/copilot-specific.instructions.md"
  assert_success
}

@test "copilot-sync: copilot-specific.instructions.md define applyTo global" {
  run grep -q 'applyTo: "\*\*"' "$REPO_ROOT/.github/copilot-specific.instructions.md"
  assert_success
}

@test "copilot-sync: instruction dedicada de doctree por repo nao e artefato versionado" {
  assert_not_exist "$REPO_ROOT/.github/copilot-doctree.instructions.md"
}

# ---------------------------------------------------------------------------
# copilot-sync.ps1 — estrutura e funcoes
# ---------------------------------------------------------------------------

@test "copilot-sync: script existe no repo" {
  assert_file_exist "$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1"
}

@test "copilot-sync: Sync-Skills copia para .copilot/skills" {
  run bash -c "grep -A 20 '^function Sync-Skills' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1' | grep -q 'Copy-Item -Path \$skillSrc.FullName -Destination \$dest -Recurse -Force'"
  assert_success
}

@test "copilot-sync: Sync-Agents materializa prompts .agent.md" {
  run bash -c "grep -A 20 '^function Sync-Agents' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1' | grep -q '\$baseName.agent.md'"
  assert_success
}

@test "copilot-sync: Sync-Commands materializa prompts .prompt.md" {
  run bash -c "grep -A 20 '^function Sync-Commands' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1' | grep -q '\$baseName.prompt.md'"
  assert_success
}

@test "copilot-sync: Sync-Instructions copia de .github/copilot-specific.instructions.md" {
  run bash -c "grep -A 12 '^function Sync-Instructions' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1' | grep -q 'copilot-specific.instructions.md'"
  assert_success
}

@test "copilot-sync: Sync-Instructions copia para .copilot/instructions" {
  run env TARGET_FILE="$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1" python3 - <<'PY'
from pathlib import Path
import os
content = Path(os.environ["TARGET_FILE"]).read_text(encoding="utf-8", errors="replace")
assert ".copilot\\instructions" in content
PY
  assert_success
}

@test "copilot-sync: Sync-Instructions NAO referencia AGENTS.md como fonte" {
  run bash -c "grep -A 12 '^function Sync-Instructions' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1' | grep -q 'AGENTS.md'"
  assert_failure
}

@test "copilot-sync: Sync-Mcp configura exa e crawl4ai" {
  run bash -c "grep -A 60 '^function Sync-Mcp' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1' | grep -q 'exa-mcp-server'"
  assert_success

  run bash -c "grep -A 60 '^function Sync-Mcp' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1' | grep -q 'http://localhost:11235/mcp/sse'"
  assert_success
}

@test "copilot-sync: Sync-McpCli configura codebase-memory sem doctree global" {
  run bash -c "grep -A 80 '^function Sync-McpCli' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1' | grep -q 'codebase-memory-mcp'"
  assert_success

  run bash -c "grep -A 80 '^function Sync-McpCli' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1' | grep -q 'doctree-run'"
  assert_failure
}

@test "copilot-sync: Show-Plan descreve a mesma cobertura funcional" {
  run env TARGET_FILE="$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1" python3 - <<'PY'
from pathlib import Path
import os
content = Path(os.environ["TARGET_FILE"]).read_text(encoding="utf-8", errors="replace")
assert "Copiar $nSkills skill(s) para .copilot\\skills\\" in content
assert "Converter $nAgents agent(s) para .agent.md" in content
assert "Copiar $nCommands command(s) para .prompt.md" in content
assert "Configurar MCPs Copilot (exa, crawl4ai) em mcp.json" in content
assert "Configurar MCPs CLI globais (crawl4ai, codebase-memory) em servers.json" in content
PY
  assert_success
}

@test "copilot-sync: Show-Plan NAO menciona copia de AGENTS.md para instructions" {
  run bash -c "grep -A 12 '^    Say \"Plano:\"' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1' | grep -q 'AGENTS.md'"
  assert_failure
}

@test "copilot-sync: AGENTS define que ambos adaptadores evoluem juntos" {
  run grep -q "adaptadores do mesmo repo" "$REPO_ROOT/AGENTS.md"
  assert_success

  run bash -c 'tr "\n" " " < "$1" | grep -q "O comportamento canonico nao pertence a apenas um deles"' _ "$REPO_ROOT/AGENTS.md"
  assert_success

  run bash -c 'tr "\n" " " < "$1" | grep -Eq "devem ser alterados[[:space:]]+juntos|devem permanecer semanticamente sincronizados e devem ser alterados[[:space:]]+juntos"' _ "$REPO_ROOT/AGENTS.md"
  assert_success
}

# ---------------------------------------------------------------------------
# Sync-DefaultArtifacts — nova funcao
# ---------------------------------------------------------------------------

@test "copilot-sync: Sync-DefaultArtifacts existe no script" {
  run bash -c "grep -q '^function Sync-DefaultArtifacts' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1'"
  assert_success
}

@test "copilot-sync: Sync-DefaultArtifacts copia default-artifacts para prompts" {
  run bash -c "grep -A 20 '^function Sync-DefaultArtifacts' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1' | grep -q 'default-artifacts'"
  assert_success
}

@test "copilot-sync: Show-Plan menciona default-artifacts" {
  run bash -c "grep -A 12 '^    Say \"Plano:\"' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1' | grep -q 'default-artifacts'"
  assert_success
}

@test "copilot-sync: main invoca Sync-DefaultArtifacts" {
  run bash -c "grep -q 'Sync-DefaultArtifacts' '$REPO_ROOT/scripts/bootstrap_repo/copilot-sync.ps1'"
  assert_success
}

# ---------------------------------------------------------------------------
# wsl-copilot-sync.sh — sync_default_artifacts
# ---------------------------------------------------------------------------

@test "copilot-sync: wsl-copilot-sync.sh contem sync_default_artifacts" {
  run bash -c "grep -q 'sync_default_artifacts()' '$REPO_ROOT/scripts/bootstrap_repo/wsl-copilot-sync.sh'"
  assert_success
}

@test "copilot-sync: wsl-copilot-sync.sh main invoca sync_default_artifacts" {
  run bash -c "grep -A 10 '^main()' '$REPO_ROOT/scripts/bootstrap_repo/wsl-copilot-sync.sh' | grep -q 'sync_default_artifacts'"
  assert_success
}

@test "copilot-sync: wsl show_plan menciona default-artifacts" {
  run bash -c "grep -A 20 '^show_plan()' '$REPO_ROOT/scripts/bootstrap_repo/wsl-copilot-sync.sh' | grep -q 'default-artifacts'"
  assert_success
}
