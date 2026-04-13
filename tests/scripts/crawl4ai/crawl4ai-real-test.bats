#!/usr/bin/env bats
# tests/mcp/crawl4ai-real.bats — valida o MCP real do Crawl4AI fora do contexto do OpenCode

load "../../helpers/test_helper"

setup()    { common_setup; }
teardown() { common_teardown; }

require_crawl4ai_real() {
  if ! curl -sf http://127.0.0.1:11235/mcp/sse >/dev/null 2>&1; then
    skip "Crawl4AI real não está disponível em http://127.0.0.1:11235"
  fi
}

@test "crawl4ai real: endpoint SSE responde quando container está ativo" {
  require_crawl4ai_real
  run curl -sfI http://127.0.0.1:11235/mcp/sse
  assert_success
}

@test "crawl4ai real: endpoint SSE expõe cabeçalho de event stream" {
  require_crawl4ai_real
  run bash -c "curl -sfI http://127.0.0.1:11235/mcp/sse | grep -i 'text/event-stream'"
  assert_success
}
