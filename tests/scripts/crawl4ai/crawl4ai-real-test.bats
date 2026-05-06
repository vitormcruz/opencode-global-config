#!/usr/bin/env bats
# tests/mcp/crawl4ai-real.bats — valida o MCP real do Crawl4AI fora do contexto do OpenCode

load "../../helpers/test_helper"

setup()    { common_setup; }
teardown() { common_teardown; }

require_crawl4ai_real() {
  if ! curl -sf --max-time 5 --connect-timeout 3 \
       http://127.0.0.1:11235/health >/dev/null 2>&1; then
    skip "Crawl4AI real não está disponível em http://127.0.0.1:11235"
  fi
}

@test "crawl4ai real: endpoint SSE responde quando container está ativo" {
  require_crawl4ai_real
  # /mcp/sse é SSE (GET only; HEAD retorna 405).
  # exit 0 = conexão encerrada pelo servidor, exit 28 = timeout (normal em SSE).
  run bash -c "
    curl -s --max-time 3 --connect-timeout 3 -D - --output /dev/null \
      http://127.0.0.1:11235/mcp/sse
    rc=\$?; [ \$rc -eq 0 ] || [ \$rc -eq 28 ]
  "
  assert_success
}

@test "crawl4ai real: endpoint SSE expõe cabeçalho de event stream" {
  require_crawl4ai_real
  # Captura cabeçalhos via -D - e filtra pelo Content-Type esperado
  run bash -c "curl -s --max-time 3 --connect-timeout 3 -D - --output /dev/null \
    http://127.0.0.1:11235/mcp/sse | grep -i 'text/event-stream'"
  assert_success
}
