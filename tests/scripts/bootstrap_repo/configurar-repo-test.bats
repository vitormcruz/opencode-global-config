#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/configurar-repo-test.bats — testa o script principal

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/bootstrap_repo/configurar-repo.sh"

setup() {
  common_setup
  export HOME="$(mktemp -d)/home"
  mkdir -p "$HOME"
}

teardown() {
  common_teardown
}

# ---------------------------------------------------------------------------
# Ajuda e opcoes
# ---------------------------------------------------------------------------

@test "configurar-repo --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
}

@test "configurar-repo --help exibe texto de uso" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "configurar-repo"
  assert_output --partial "Uso:"
  assert_output --partial "Instala dependencias WSL"
  assert_output --partial "Executa o adapter Copilot CLI"
  assert_output --partial "Executa o adapter OpenCode"
  assert_output --partial "Instala ferramentas globais"
}

@test "configurar-repo com opcao invalida retorna exit 2" {
  run bash "$SCRIPT" --flag-invalido
  assert_failure
  [ "$status" -eq 2 ]
}

@test "configurar-repo retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
}

# ---------------------------------------------------------------------------
# Variaveis de ambiente SKIP
# ---------------------------------------------------------------------------

@test "configurar-repo respeita OPENCODE_SKIP_DEPS=1" {
  # Quando pula deps, ainda tenta rodar as outras partes
  export OPENCODE_SKIP_DEPS=1
  export OPENCODE_SKIP_COPILOT_ADAPTER=1
  export OPENCODE_SKIP_OPENCODE_ADAPTER=1
  export OPENCODE_SKIP_CODEBASE_MEMORY=1

  run bash "$SCRIPT" --quiet
  assert_success
}

@test "configurar-repo respeita OPENCODE_SKIP_COPILOT_ADAPTER=1" {
  export OPENCODE_SKIP_COPILOT_ADAPTER=1
  export OPENCODE_SKIP_OPENCODE_ADAPTER=1
  export OPENCODE_SKIP_CODEBASE_MEMORY=1

  run bash "$SCRIPT" --quiet
  assert_success
}

@test "configurar-repo respeita OPENCODE_SKIP_OPENCODE_ADAPTER=1" {
  export OPENCODE_SKIP_OPENCODE_ADAPTER=1
  export OPENCODE_SKIP_CODEBASE_MEMORY=1

  run bash "$SCRIPT" --quiet
  assert_success
}

# ---------------------------------------------------------------------------
# Variaveis de ambiente SKIP para ferramentas globais
# ---------------------------------------------------------------------------

@test "configurar-repo respeita OPENCODE_SKIP_CODEBASE_MEMORY=1" {
  export OPENCODE_SKIP_CODEBASE_MEMORY=1
  export OPENCODE_SKIP_DEPS=1
  export OPENCODE_SKIP_COPILOT_ADAPTER=1
  export OPENCODE_SKIP_OPENCODE_ADAPTER=1

  run bash "$SCRIPT" --quiet
  assert_success
}

@test "configurar-repo --help exibe ferramentas globais" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "codebase-memory"
}

@test "configurar-repo nao referencia configuracao MCP removida" {
  run grep -Eq 'servers\.json|OPENCODE_SKIP_CRAWL4AI|run_crawl4ai' "$SCRIPT"
  assert_failure
}
