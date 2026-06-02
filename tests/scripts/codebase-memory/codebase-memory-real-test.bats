#!/usr/bin/env bats
# tests/scripts/codebase-memory/codebase-memory-real-test.bats
# Valida o MCP real do codebase-memory via stdio

load "../../helpers/test_helper"

setup()    { common_setup; }
teardown() { common_teardown; }

require_codebase_memory_real() {
  if ! command -v codebase-memory-mcp >/dev/null 2>&1; then
    fail "codebase-memory-mcp nao disponivel neste ambiente — instale codebase-memory-mcp para executar este teste"
  fi
  # Verificar se o binário realmente consegue executar (pode existir no PATH mas
  # falhar por incompatibilidade de bibliotecas, ex: GLIBC/GLIBCXX diferente)
  run codebase-memory-mcp --version 2>&1
  if [[ "$status" -ne 0 ]]; then
    fail "codebase-memory-mcp existe no PATH mas não executa. Saída: $output"
  fi
}

@test "codebase-memory real: binario responde a --help" {
  require_codebase_memory_real
  run codebase-memory-mcp --help
  assert_success
}

@test "codebase-memory real: binario aceita comando version" {
  require_codebase_memory_real
  run codebase-memory-mcp --version
  assert_success
}
