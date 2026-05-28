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

@test "doctree real: bunx doctree-mcp responde a --version" {
  require_doctree_real
  local tmpdir
  tmpdir="$(mktemp -d)"
  mkdir -p "$tmpdir/docs"
  run env DOCS_ROOT="$tmpdir/docs" bunx doctree-mcp --version </dev/null
  assert_success
  rm -rf "$tmpdir"
}
