#!/usr/bin/env bats
# tests/scripts/doctree/doctree-real-test.bats
# Valida o MCP real do doctree via bunx stdio

load "../../helpers/test_helper"

setup()    { common_setup; }
teardown() { common_teardown; }

require_doctree_real() {
  if ! command -v bunx >/dev/null 2>&1; then
    fail "bunx nao disponivel neste ambiente — instale bun para executar este teste"
  fi
}

@test "doctree real: bunx consegue resolver doctree-mcp" {
  require_doctree_real
  local tmpdir
  tmpdir="$(mktemp -d)"
  mkdir -p "$tmpdir/docs"
  run env DOCS_ROOT="$tmpdir/docs" bunx doctree-mcp --help </dev/null
  assert_success
  rm -rf "$tmpdir"
}

@test "doctree real: bunx doctree-mcp responde a tools/list via protocolo MCP" {
  require_doctree_real
  local tmpdir
  tmpdir="$(mktemp -d)"
  mkdir -p "$tmpdir/docs"
  echo "# Test Doc" > "$tmpdir/docs/test.md"

  # MCP stdio requer handshake: initialize primeiro, depois tools/list
  run bash -c "printf '%s\n%s\n' \
    '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"test\",\"version\":\"0\"}}}' \
    '{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\",\"params\":{}}' \
    | env DOCS_ROOT='$tmpdir/docs' timeout 10 bunx doctree-mcp 2>/dev/null"

  assert_success
  assert_output --partial '"tools"'
  assert_output --partial 'list_documents'
  rm -rf "$tmpdir"
}
