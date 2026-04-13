#!/usr/bin/env bash
# tests/opencode-int-test/behavioral_helper.bash — helpers da integração do OpenCode

BATS_LIB_PATH="${BATS_LIB_PATH:-$HOME/.local/lib/bats}"
export BATS_LIB_PATH

bats_load_library bats-support
bats_load_library bats-assert

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_ENV="$REPO_ROOT/tests/opencode-int-test/.test-env"

OPENCODE_PORT="${OPENCODE_PORT:-4196}"
OPENCODE_BASE_URL="http://127.0.0.1:${OPENCODE_PORT}"

load_test_model() {
  if [[ -f "$TEST_ENV" ]]; then
    # shellcheck source=/dev/null
    source "$TEST_ENV"
  fi
}

# Verifica se o container está disponível antes de executar testes
require_opencode_serve() {
  if ! curl -sf "${OPENCODE_BASE_URL}/" &>/dev/null; then
    skip "OpenCode serve não está disponível em ${OPENCODE_BASE_URL}. Execute: bash tests/opencode-int-test/container-test-opencode.sh --up"
  fi
}

# Cria uma sessão e retorna o ID
create_session() {
  load_test_model
  curl -sf -X POST "${OPENCODE_BASE_URL}/session" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"${OPENCODE_TEST_MODEL:-opencode/big-pickle}\"}" \
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
