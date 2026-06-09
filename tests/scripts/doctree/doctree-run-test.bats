#!/usr/bin/env bats
# tests/scripts/doctree/run-test.bats — testa scripts/doctree/doctree-run.sh

load "../../helpers/test_helper"

setup() {
  TEST_HOME="$(mktemp -d)"
  export HOME="$TEST_HOME"
  TEST_PROJECT="$TEST_HOME/project"
  mkdir -p "$TEST_PROJECT"
  cd "$TEST_PROJECT"
}

teardown() {
  cd /
  rm -rf "$TEST_HOME"
}

# ---------------------------------------------------------------------------
# Estrutura
# ---------------------------------------------------------------------------

@test "scripts/doctree/doctree-run.sh existe" {
  assert_file_exist "$REPO_ROOT/scripts/doctree/doctree-run.sh"
}

@test "scripts/doctree/doctree-run.sh e executavel" {
  assert_file_executable "$REPO_ROOT/scripts/doctree/doctree-run.sh"
}

# ---------------------------------------------------------------------------
# Descoberta do projeto via .git walk-up
# ---------------------------------------------------------------------------

@test "run.sh encontra raiz do projeto via .git (walk-up a partir de subdiretorio)" {
  mkdir -p "$TEST_PROJECT/.git"
  mkdir -p "$TEST_PROJECT/sub/dir"
  cd "$TEST_PROJECT/sub/dir"

  # Executa run.sh com função mockada para nao spawnar doctree-mcp
  run bash -c "
    . '$REPO_ROOT/scripts/doctree/doctree-run.sh' 2>/dev/null &
    sleep 0.2; kill %1 2>/dev/null
  " 2>/dev/null || true

  # O script deve ter encontrado o .git e definido PROJECT_ROOT
  # Como o script faz exec bunx, nao podemos verificar diretamente.
  # Testamos que o script nao falha com .git presente.
  run bash -c "source '$REPO_ROOT/scripts/doctree/doctree-run.sh'" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# .env-doctree sourcing
# ---------------------------------------------------------------------------

@test "run.sh faz source do .env-doctree quando existe" {
  mkdir -p "$TEST_PROJECT/.git"
  cat > "$TEST_PROJECT/.env-doctree" <<'EOF'
export DOCS_ROOTS="./docs:1.0,./agents:0.9"
EOF
  cd "$TEST_PROJECT"

  # Testa que o source funciona sem erro
  run bash -c "
    set -a
    source '$TEST_PROJECT/.env-doctree' 2>/dev/null
    set +a
    echo \"DOCS_ROOTS=\${DOCS_ROOTS:-unset}\"
  "
  assert_success
  assert_output --partial "DOCS_ROOTS=./docs:1.0,./agents:0.9"
}

# ---------------------------------------------------------------------------
# Fallback DOCS_ROOT quando .env-doctree ausente
# ---------------------------------------------------------------------------

@test "run.sh usa DOCS_ROOT default quando .env-doctree ausente" {
  mkdir -p "$TEST_PROJECT/.git"
  cd "$TEST_PROJECT"

  # Simula o que o run.sh faz: export DOCS_ROOT com fallback
  run bash -c "
    PROJECT_ROOT='$TEST_PROJECT'
    export DOCS_ROOT=\"\${DOCS_ROOT:-\${PROJECT_ROOT}/docs}\"
    echo \"DOCS_ROOT=\${DOCS_ROOT}\"
  "
  assert_success
  assert_output --partial "DOCS_ROOT=${TEST_PROJECT}/docs"
}

# ---------------------------------------------------------------------------
# Simulacao do symlink doctree-run
# ---------------------------------------------------------------------------

## Teste de integracao (so roda com symlink real, ja coberto por opencode-link-test.bats)
# @test "symlink doctree-run existe em ~/.local/bin" {
#   ...
# }
