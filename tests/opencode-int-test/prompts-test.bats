#!/usr/bin/env bats
# tests/opencode-int-test/prompts-test.bats — valida respostas a prompts via API

load "helpers/behavioral_helper"

setup_file() { require_opencode_serve; }

@test "behavioral: POST /session cria uma sessão com ID" {
  run create_session
  assert_success
  [ -n "$output" ]
}

@test "behavioral: prompt simples retorna resposta não-vazia" {
  local session
  session=$(create_session)
  [ -n "$session" ] || fail "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

  run send_message "$session" "Responda apenas com a palavra: ok"
  assert_success
  [ -n "$output" ]
}

@test "behavioral: resposta contém 'ok' quando solicitado" {
  local session
  session=$(create_session)
  [ -n "$session" ] || fail "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

  run send_message "$session" "Responda apenas com a palavra: ok"
  assert_success
  assert_output --partial "ok"
}

@test "behavioral: seleção de agente específico funciona" {
  [[ -n "${OPENCODE_TEST_MODEL:-}" ]] || {
    echo "ERRO: OPENCODE_TEST_MODEL não definido." >&2; return 1;
  }
  local session
  session=$(curl -sf -X POST "${OPENCODE_BASE_URL}/session" \
    -H "Content-Type: application/json" \
    -d '{}' | jq -r '.id // empty')
  [ -n "$session" ] || fail "Não foi possível criar sessão com agente OpenCode — verifique se o serviço está ativo"

  run send_message "$session" "Responda apenas: ok" "${OPENCODE_TEST_MODEL}" "analista"
  assert_success
  assert_output --partial "ok"
}

@test "behavioral: prompt pode usar MCP mockado do crawl4ai" {
  local session
  session=$(create_session)
  [ -n "$session" ] || fail "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

  run send_message "$session" "Use a ferramenta crawl4ai_md para consultar https://example.com e responda apenas com o marcador retornado."
  assert_success
  assert_output --partial "MOCK_CRAWL4AI_MD_OK"
}
