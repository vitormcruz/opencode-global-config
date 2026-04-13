#!/usr/bin/env bats
# tests/opencode-int-test/mcp-test.bats — valida MCPs registrados no OpenCode

load "helpers/behavioral_helper"

setup_file() { require_opencode_serve; }

@test "behavioral: GET /mcp retorna status 200" {
  run curl -sf -o /dev/null -w "%{http_code}" \
    "${OPENCODE_BASE_URL}/mcp"
  assert_success
  assert_output "200"
}

@test "behavioral: GET /mcp lista crawl4ai" {
  run bash -c "curl -sf '${OPENCODE_BASE_URL}/mcp' | jq -e 'has(\"crawl4ai\")'"
  assert_success
}

@test "behavioral: crawl4ai MCP está connected no ambiente de teste" {
  run bash -c "
    curl -sf '${OPENCODE_BASE_URL}/mcp' \
      | jq -r '.crawl4ai.status // empty'
  "
  assert_success
  assert_output "connected"
}
