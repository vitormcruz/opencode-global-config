#!/usr/bin/env bats
# tests/crawl4ai/install-crawl4ai-mcp.bats — testa o script de instalação
# do Crawl4AI MCP (responsabilidade única: só altera ~/.bashrc)

load "../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/crawl4ai/install-crawl4ai-mcp.sh"

setup()    { common_setup; }
teardown() { common_teardown; }

# ---------------------------------------------------------------------------
# Helpers: cria mock completo do docker no fake_bin
# ---------------------------------------------------------------------------

_make_fake_bin_no_docker() {
  local fake_bin="$1"
  # Copia comandos essenciais (sem docker)
  for cmd in bash sh grep sed cat chmod mkdir touch; do
    local p
    p="$(command -v "$cmd" 2>/dev/null)" || continue
    ln -sf "$p" "$fake_bin/$cmd"
  done
}

_make_docker_mock() {
  local fake_bin="$1"
  local info_exit="${2:-0}"   # exit code de `docker info`
  local pull_exit="${3:-0}"   # exit code de `docker pull`

  cat > "$fake_bin/docker" << MOCK
#!/bin/bash
case "\$1" in
  info)  exit $info_exit ;;
  pull)  exit $pull_exit ;;
  build) exit 0 ;;
  run)   exit 0 ;;
  rm)    exit 0 ;;
  ps)    echo "" ; exit 0 ;;
  *)     exit 0 ;;
esac
MOCK
  chmod +x "$fake_bin/docker"
}

# ---------------------------------------------------------------------------
# Docker indisponível → aborta com erro
# ---------------------------------------------------------------------------

@test "script aborta se docker não está instalado" {
  local fake_bin
  fake_bin="$(mktemp -d)"
  _make_fake_bin_no_docker "$fake_bin"
  # Sem docker no fake_bin

  run bash -c "
    PATH='$fake_bin'
    bash '$SCRIPT' 2>&1
  "
  assert_failure
  assert_output --partial "Docker"

  rm -rf "$fake_bin"
}

@test "script aborta se docker não está em execução" {
  local fake_bin
  fake_bin="$(mktemp -d)"
  _make_fake_bin_no_docker "$fake_bin"
  _make_docker_mock "$fake_bin" 1 0   # info retorna exit 1

  run bash -c "
    PATH='$fake_bin'
    bash '$SCRIPT' 2>&1
  "
  assert_failure
  assert_output --partial "execução"

  rm -rf "$fake_bin"
}

# ---------------------------------------------------------------------------
# Não cria nem modifica arquivos em ~/.config/opencode/
# ---------------------------------------------------------------------------

@test "script não cria ~/.config/opencode/ quando docker está ausente" {
  local fake_bin
  fake_bin="$(mktemp -d)"
  _make_fake_bin_no_docker "$fake_bin"

  HOME="$TEST_HOME" PATH="$fake_bin" bash "$SCRIPT" 2>&1 || true

  assert_not_exist "$TEST_CONFIG_DIR"
  rm -rf "$fake_bin"
}

@test "script não cria AGENTS.md em ~/.config/opencode/ (docker ausente)" {
  local fake_bin
  fake_bin="$(mktemp -d)"
  _make_fake_bin_no_docker "$fake_bin"

  HOME="$TEST_HOME" PATH="$fake_bin" bash "$SCRIPT" 2>&1 || true

  assert_not_exist "$TEST_CONFIG_DIR/AGENTS.md"
  rm -rf "$fake_bin"
}

@test "script não cria opencode.json em ~/.config/opencode/ (docker ausente)" {
  local fake_bin
  fake_bin="$(mktemp -d)"
  _make_fake_bin_no_docker "$fake_bin"

  HOME="$TEST_HOME" PATH="$fake_bin" bash "$SCRIPT" 2>&1 || true

  assert_not_exist "$TEST_CONFIG_DIR/opencode.json"
  rm -rf "$fake_bin"
}

@test "script não cria scripts/ em ~/.config/opencode/ (docker ausente)" {
  local fake_bin
  fake_bin="$(mktemp -d)"
  _make_fake_bin_no_docker "$fake_bin"

  HOME="$TEST_HOME" PATH="$fake_bin" bash "$SCRIPT" 2>&1 || true

  assert_not_exist "$TEST_CONFIG_DIR/scripts"
  rm -rf "$fake_bin"
}

# ---------------------------------------------------------------------------
# .bashrc — bloco com markers, idempotente
# (testado via lógica isolada, sem depender de docker)
# ---------------------------------------------------------------------------

@test "lógica de .bashrc adiciona bloco com markers corretos" {
  run bash -c "
    BASHRC='$TEST_BASHRC'
    MARKER_START='# Crawl4AI MCP - INICIO'
    MARKER_END='# Crawl4AI MCP - FIM'

    if grep -q \"\$MARKER_START\" \"\$BASHRC\" 2>/dev/null; then
      sed -i \"/\$MARKER_START/,/\$MARKER_END/d\" \"\$BASHRC\"
    fi

    printf '\n%s\n# content\n%s\n' \"\$MARKER_START\" \"\$MARKER_END\" >> \"\$BASHRC\"

    grep -q \"\$MARKER_START\" \"\$BASHRC\" && echo 'marker_found'
  "
  assert_success
  assert_output "marker_found"
}

@test "lógica de .bashrc não duplica bloco ao rodar 2x" {
  run bash -c "
    BASHRC='$TEST_BASHRC'
    MARKER_START='# Crawl4AI MCP - INICIO'
    MARKER_END='# Crawl4AI MCP - FIM'

    _add_block() {
      if grep -q \"\$MARKER_START\" \"\$BASHRC\" 2>/dev/null; then
        sed -i \"/\$MARKER_START/,/\$MARKER_END/d\" \"\$BASHRC\"
      fi
      printf '\n%s\n# content\n%s\n' \"\$MARKER_START\" \"\$MARKER_END\" >> \"\$BASHRC\"
    }

    _add_block
    _add_block

    count=\$(grep -c \"\$MARKER_START\" \"\$BASHRC\")
    echo \"\$count\"
  "
  assert_success
  assert_output "1"
}
