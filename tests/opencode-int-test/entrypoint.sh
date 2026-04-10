#!/usr/bin/env bash
set -euo pipefail

cleanup() {
  if [[ -n "${MCP_MOCK_PID:-}" ]]; then
    kill "$MCP_MOCK_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

node /opt/opencode-config/tests/opencode-int-test/mcp-mock/server.js &
MCP_MOCK_PID=$!

for _ in $(seq 1 30); do
  if curl -sf http://127.0.0.1:11235/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

exec /root/.opencode/bin/opencode --pure serve --hostname 0.0.0.0 --port 4096
