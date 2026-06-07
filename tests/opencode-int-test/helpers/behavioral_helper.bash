#!/usr/bin/env bash
# tests/opencode-int-test/helpers/behavioral_helper.bash — helpers da integração do OpenCode

BATS_LIB_PATH="${BATS_LIB_PATH:-$HOME/.local/lib/bats}"
export BATS_LIB_PATH

bats_load_library bats-support
bats_load_library bats-assert

OPENCODE_PORT="${OPENCODE_PORT:-4196}"
OPENCODE_BASE_URL="http://127.0.0.1:${OPENCODE_PORT}"

# Verifica se o container está disponível antes de executar testes
require_opencode_serve() {
  if ! curl -sf "${OPENCODE_BASE_URL}/" &>/dev/null; then
    fail "OpenCode serve não está disponível em ${OPENCODE_BASE_URL}. Execute: bash tests/opencode-int-test/docker/container-test-opencode.sh --up"
  fi
}

# Cria uma sessão e retorna o ID
# Exige OPENCODE_TEST_MODEL definido — sem fallback
# Nota: a API POST /session so aceita parentID/title; o modelo usado e o
# configurado no opencode.json do servidor (substituido pelo entrypoint).
create_session() {
  if [[ -z "${OPENCODE_TEST_MODEL:-}" ]]; then
    echo "ERRO: OPENCODE_TEST_MODEL não definido. Defina o modelo antes de rodar testes." >&2
    return 1
  fi
  curl -sf -X POST "${OPENCODE_BASE_URL}/session" \
    -H "Content-Type: application/json" \
    -d '{}' \
    | jq -r '.id // empty'
}

# Envia mensagem e retorna o texto da resposta (parts[].text onde type=="text")
# Se model for informado (formato "provider/model"), envia como objeto
# {providerID, modelID} no body. Senao, omite e o servidor usa o config.
send_message() {
  set -o pipefail
  local session_id="$1"
  local text="$2"
  local model="${3:-}"
  local agent="${4:-}"
  local model_json=""
  if [[ -n "$model" ]]; then
    local provider_id="${model%%/*}"
    local model_id="${model#*/}"
    model_json=",\"model\":{\"providerID\":\"${provider_id}\",\"modelID\":\"${model_id}\"}"
  fi
  local agent_json=""
  if [[ -n "$agent" ]]; then
    agent_json=",\"agent\":\"${agent}\""
  fi
  local response
  response=$(curl -sf -X POST \
    "${OPENCODE_BASE_URL}/session/${session_id}/message" \
    -H "Content-Type: application/json" \
    -d "{\"parts\":[{\"type\":\"text\",\"text\":\"${text}\"}]${model_json}${agent_json}}") || {
    echo "ERRO: curl falhou ao enviar mensagem para sessao ${session_id}" >&2
    return 1
  }

  if echo "$response" | jq -e 'has("_tag") or has("error")' >/dev/null 2>&1; then
    echo "ERRO: ${response}" >&2
    return 1
  fi

  echo "$response" | jq -r '.parts[] | select(.type=="text") | .text // empty' | tr -d '\n'
}
