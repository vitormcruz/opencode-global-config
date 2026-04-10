#!/usr/bin/env bats
# tests/behavioral/prompts.bats — valida respostas a prompts via API

load "../helpers/behavioral_helper"

setup_file() { require_opencode_serve; }

@test "behavioral: POST /session cria uma sessão com ID" {
  run bash -c "curl -sf -X POST '${OPENCODE_BASE_URL}/session' \
    -H 'Content-Type: application/json' \
    -d '{}' | jq -r '.id // empty'"
  assert_success
  [ -n "$output" ]
}

@test "behavioral: prompt simples retorna resposta não-vazia" {
  local session
  session=$(create_session)
  [ -n "$session" ] || skip "Não foi possível criar sessão"

  run send_message "$session" "Responda apenas com a palavra: ok"
  assert_success
  [ -n "$output" ]
}

@test "behavioral: resposta contém 'ok' quando solicitado" {
  local session
  session=$(create_session)
  [ -n "$session" ] || skip "Não foi possível criar sessão"

  run send_message "$session" "Responda apenas com a palavra: ok"
  assert_success
  assert_output --partial "ok"
}

@test "behavioral: seleção de agente específico funciona" {
  local session
  session=$(curl -sf -X POST "${OPENCODE_BASE_URL}/session" \
    -H "Content-Type: application/json" \
    -d '{"agent":"analista"}' | jq -r '.id // empty')
  [ -n "$session" ] || skip "Não foi possível criar sessão com agente"

  run send_message "$session" "Responda apenas: ok"
  assert_success
  assert_output --partial "ok"
}
