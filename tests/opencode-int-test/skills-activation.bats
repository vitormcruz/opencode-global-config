#!/usr/bin/env bats
# tests/opencode-int-test/skills-activation.bats — valida ativação de skills via prompt

load "behavioral_helper"

setup_file() { require_opencode_serve; }

@test "behavioral: prompt que menciona doc-extract recebe resposta coerente" {
  local session
  session=$(create_session)
  [ -n "$session" ] || skip "Não foi possível criar sessão"

  run send_message "$session" \
    "Existe uma skill chamada doc-extract? Responda apenas sim ou nao."
  assert_success
  run bash -c "echo '$output' | grep -qi 'sim'"
  assert_success
}

@test "behavioral: prompt que menciona md-export recebe resposta coerente" {
  local session
  session=$(create_session)
  [ -n "$session" ] || skip "Não foi possível criar sessão"

  run send_message "$session" \
    "Existe uma skill chamada md-export? Responda apenas sim ou nao."
  assert_success
  run bash -c "echo '$output' | grep -qi 'sim'"
  assert_success
}

@test "behavioral: skill svg-to-image é mencionável sem erro" {
  local session
  session=$(create_session)
  [ -n "$session" ] || skip "Não foi possível criar sessão"

  run send_message "$session" \
    "Existe uma skill chamada svg-to-image? Responda sim ou não."
  assert_success
  # Aceita "sim" ou "Sim" (case-insensitive)
  run bash -c "echo '$output' | grep -qi 'sim'"
  assert_success
}
