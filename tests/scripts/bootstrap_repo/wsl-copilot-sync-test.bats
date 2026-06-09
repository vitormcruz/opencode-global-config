#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/wsl-copilot-sync-test.bats — testa sincronizacao Copilot

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/bootstrap_repo/wsl-copilot-sync.sh"

setup() {
  common_setup
  export HOME="$(mktemp -d)/home"
  export USER="ur5y"
   mkdir -p "$HOME/.copilot" "$HOME/.vscode-server/data/User"
}

teardown() {
  common_teardown
}

# ---------------------------------------------------------------------------
# Ajuda e opcoes
# ---------------------------------------------------------------------------

@test "wsl-copilot-sync --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
}

@test "wsl-copilot-sync --help exibe texto de uso" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "wsl-copilot-sync"
  assert_output --partial "Uso:"
}

@test "wsl-copilot-sync com opcao invalida retorna exit 2" {
  run bash "$SCRIPT" --invalido
  assert_failure
  [ "$status" -eq 2 ]
}

# ---------------------------------------------------------------------------
# Funcionalidade de sincronizacao
# ---------------------------------------------------------------------------

@test "wsl-copilot-sync --yes funciona sem TTY" {
  run bash "$SCRIPT" --yes
  assert_success
}

@test "wsl-copilot-sync copia skills para ~/.copilot/skills" {
  run bash "$SCRIPT" --yes
  assert_success
  [ -d "$HOME/.copilot/skills" ]
  [ -f "$HOME/.copilot/skills/browser-testing/SKILL.md" ]
}

@test "wsl-copilot-sync materializa agents em prompts/*.agent.md" {
  run bash "$SCRIPT" --yes
  assert_success
  [ -f "$HOME/.vscode-server/data/User/prompts/eng-software.agent.md" ]
}

@test "wsl-copilot-sync materializa commands em prompts/*.prompt.md" {
  run bash "$SCRIPT" --yes
  assert_success
  [ -f "$HOME/.vscode-server/data/User/prompts/index-codebase.prompt.md" ]
}

@test "wsl-copilot-sync espelha prompts para Windows quando detectado" {
  mkdir -p "/mnt/c/Users/$USER/AppData/Roaming/Code/User/prompts"
  run bash "$SCRIPT" --yes
  assert_success
  [ -f "/mnt/c/Users/$USER/AppData/Roaming/Code/User/prompts/index-codebase.prompt.md" ]
}

@test "wsl-copilot-sync mantem opencode-config.instructions.md no destino Windows" {
  mkdir -p "/mnt/c/Users/$USER/AppData/Roaming/Code/User/prompts"
  run bash "$SCRIPT" --yes
  assert_success
  [ -f "/mnt/c/Users/$USER/AppData/Roaming/Code/User/prompts/opencode-config.instructions.md" ]
}

@test "wsl-copilot-sync copia instructions para ~/.copilot/instructions" {
  run bash "$SCRIPT" --yes
  assert_success
  [ -f "$HOME/.copilot/instructions/copilot-specific.instructions.md" ]
}

@test "wsl-copilot-sync configura mcp.json no destino do VS Code" {
  run bash "$SCRIPT" --yes
  assert_success
  [ -f "$HOME/.vscode-server/data/User/mcp.json" ]
  run grep -q '"exa"' "$HOME/.vscode-server/data/User/mcp.json"
  assert_success
  run grep -q '"crawl4ai"' "$HOME/.vscode-server/data/User/mcp.json"
  assert_success
}

@test "wsl-copilot-sync configura servers.json do CLI mcp" {
  run bash "$SCRIPT" --yes
  assert_success
  [ -f "$HOME/.config/mcp/servers.json" ]
  run grep -q '"codebase-memory"' "$HOME/.config/mcp/servers.json"
  assert_success
  run grep -q '"crawl4ai"' "$HOME/.config/mcp/servers.json"
  assert_success
  run grep -q '"doctree"' "$HOME/.config/mcp/servers.json"
  assert_failure
}

@test "wsl-copilot-sync preserva entradas existentes em servers.json" {
  mkdir -p "$HOME/.config/mcp"
  cat > "$HOME/.config/mcp/servers.json" <<'EOF'
{
  "servers": {
    "custom": {
      "command": "custom-mcp",
      "args": ["--stdio"]
    }
  }
}
EOF

  run bash "$SCRIPT" --yes
  assert_success
  run grep -q '"custom"' "$HOME/.config/mcp/servers.json"
  assert_success
  run grep -q '"codebase-memory"' "$HOME/.config/mcp/servers.json"
  assert_success
}

@test "wsl-copilot-sync nao reintroduz doctree global legado em servers.json" {
  mkdir -p "$HOME/.config/mcp"
  cat > "$HOME/.config/mcp/servers.json" <<'EOF'
{
  "servers": {
    "doctree": {
      "command": "bunx",
      "args": ["doctree-mcp"]
    }
  }
}
EOF

  run bash "$SCRIPT" --yes
  assert_success
  run grep -c '"doctree"' "$HOME/.config/mcp/servers.json"
  assert_success
  [ "$output" -eq 1 ]
  run grep -q '"doctree-run"' "$HOME/.config/mcp/servers.json"
  assert_failure
}

@test "wsl-copilot-sync: AGENTS define canonico compartilhado entre adaptadores" {
  run grep -q "wsl-copilot-sync.sh" "$REPO_ROOT/AGENTS.md"
  assert_success

  run grep -q "copilot-sync.ps1" "$REPO_ROOT/AGENTS.md"
  assert_success

  run bash -c 'tr "\n" " " < "$1" | grep -q "O comportamento canonico nao pertence a apenas um deles"' _ "$REPO_ROOT/AGENTS.md"
  assert_success

  run bash -c 'tr "\n" " " < "$1" | grep -Eq "devem ser alterados[[:space:]]+juntos|devem permanecer semanticamente sincronizados e devem ser alterados[[:space:]]+juntos"' _ "$REPO_ROOT/AGENTS.md"
  assert_success
}
