#!/usr/bin/env bash
# tests/helpers/behavioral_helper.bash — helpers para testes da Camada 2 (Docker)

BATS_LIBS_DIR="$(dirname "${BASH_SOURCE[0]}")/../bats-libs"
load "$BATS_LIBS_DIR/bats-support/load.bash"
load "$BATS_LIBS_DIR/bats-assert/load.bash"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_ENV="$REPO_ROOT/tests/.test-env"

OPENCODE_PORT="${OPENCODE_PORT:-4096}"
OPENCODE_BASE_URL="http://localhost:${OPENCODE_PORT}"

# Verifica se o container está disponível antes de executar testes
require_opencode_serve() {
  if ! curl -sf "${OPENCODE_BASE_URL}/" &>/dev/null; then
    skip "OpenCode serve não está disponível em ${OPENCODE_BASE_URL}. Execute: bash tests/setup-container.sh"
  fi
}

# Cria uma sessão e retorna o ID
create_session() {
  curl -sf -X POST "${OPENCODE_BASE_URL}/session" \
    -H "Content-Type: application/json" \
    -d '{}' \
    | jq -r '.id // empty'
}

# Envia mensagem e retorna o texto da resposta (parts[].text onde type=="text")
send_message() {
  local session_id="$1"
  local text="$2"
  curl -sf -X POST \
    "${OPENCODE_BASE_URL}/session/${session_id}/message" \
    -H "Content-Type: application/json" \
    -d "{\"parts\":[{\"type\":\"text\",\"text\":\"${text}\"}]}" \
    | jq -r '.parts[] | select(.type=="text") | .text // empty' \
    | tr -d '\n'
}
