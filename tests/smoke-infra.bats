#!/usr/bin/env bats
# tests/smoke-infra.bats — valida que a infra BATS está funcionando

load "helpers/test_helper"

@test "infra BATS está operacional" {
  run echo "ok"
  assert_success
  assert_output "ok"
}
