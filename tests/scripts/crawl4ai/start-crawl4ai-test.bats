#!/usr/bin/env bats

load "../../helpers/test_helper"

setup() {
  common_setup
}

teardown() {
  common_teardown
}

SCRIPT="$REPO_ROOT/scripts/crawl4ai/start-crawl4ai.sh"

@test "start-crawl4ai publica token no container" {
  run grep -q 'CRAWL4AI_TOKEN=' "$SCRIPT"
  assert_success
  run grep -q -- '-e "CRAWL4AI_API_TOKEN=' "$SCRIPT"
  assert_success
}

@test "start-crawl4ai verifica health com Authorization" {
  run grep -q 'Authorization: Bearer' "$SCRIPT"
  assert_success
  run grep -q 'crawl4ai-wait' "$SCRIPT"
  assert_success
}
