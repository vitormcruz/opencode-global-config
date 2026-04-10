#!/usr/bin/env bats
# tests/behavioral/commands.bats — valida slash commands registrados no OpenCode

load "../helpers/behavioral_helper"

setup_file() { require_opencode_serve; }

@test "behavioral: GET /command retorna status 200" {
  run curl -sf -o /dev/null -w "%{http_code}" \
    "${OPENCODE_BASE_URL}/command"
  assert_success
  assert_output "200"
}

@test "behavioral: GET /command lista sync-upstream-skills" {
  run bash -c "curl -sf '${OPENCODE_BASE_URL}/command' | jq -e '[.[].name] | contains([\"sync-upstream-skills\"])'"
  assert_success
}

@test "behavioral: sync-upstream-skills tem campo de descrição" {
  run bash -c "
    curl -sf '${OPENCODE_BASE_URL}/command' \
      | jq -e '.[] | select(.name == \"sync-upstream-skills\") | has(\"description\")'
  "
  assert_success
}
