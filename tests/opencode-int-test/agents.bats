#!/usr/bin/env bats
# tests/opencode-int-test/agents.bats — valida agentes carregados pelo OpenCode

load "behavioral_helper"

setup_file() { require_opencode_serve; }

@test "behavioral: GET /agent retorna status 200" {
  run curl -sf -o /dev/null -w "%{http_code}" \
    "${OPENCODE_BASE_URL}/agent"
  assert_success
  assert_output "200"
}

@test "behavioral: GET /agent lista o agente analista-bd" {
  run curl -sf "${OPENCODE_BASE_URL}/agent"
  assert_success
  assert_output --partial "analista-bd"
}

@test "behavioral: GET /agent lista o agente revisor-historia" {
  run curl -sf "${OPENCODE_BASE_URL}/agent"
  assert_success
  assert_output --partial "revisor-historia"
}

@test "behavioral: GET /agent lista o agente analista" {
  run curl -sf "${OPENCODE_BASE_URL}/agent"
  assert_success
  assert_output --partial "analista"
}

@test "behavioral: GET /agent lista o agente aws-analista" {
  run curl -sf "${OPENCODE_BASE_URL}/agent"
  assert_success
  assert_output --partial "aws-analista"
}

@test "behavioral: cada agente retornado tem campo 'name'" {
  run bash -c "
    curl -sf '${OPENCODE_BASE_URL}/agent' \
      | jq -e 'if type == \"array\" then all(.[]; has(\"name\")) else has(\"name\") end'
  "
  assert_success
}
