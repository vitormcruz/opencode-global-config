#!/usr/bin/env bats
# tests/skills/web-research-exa-crawl4ai-test.bats — valida skill web-research-exa-crawl4ai

load "../helpers/test_helper"

@test "web-research-exa-crawl4ai/SKILL.md existe" {
  assert_file_exist "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
}

@test "web-research-exa-crawl4ai SKILL.md tem frontmatter com name" {
  run grep "^name:" "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
  assert_success
  assert_output --partial "web-research-exa-crawl4ai"
}

@test "web-research-exa-crawl4ai SKILL.md tem frontmatter com description" {
  run grep "^description:" "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
  assert_success
}

@test "web-research-exa-crawl4ai SKILL.md menciona websearch no corpo" {
  run grep -c "websearch" "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "web-research-exa-crawl4ai SKILL.md menciona crawl4ai no corpo" {
  run grep -c "crawl4ai" "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "web-research-exa-crawl4ai SKILL.md tem secao Regras principais" {
  run grep -c "Regras principais" "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "web-research-exa-crawl4ai SKILL.md tem secao Resiliencia a rate limits" {
  run grep -c "Resiliencia a rate limits" "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "web-research-exa-crawl4ai SKILL.md menciona NUNCA desista da pesquisa" {
  run grep -c "NUNCA desista da pesquisa" "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "web-research-exa-crawl4ai SKILL.md menciona backoff progressivo" {
  run grep -c "backoff progressivo" "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "web-research-exa-crawl4ai SKILL.md menciona 429" {
  run grep -c "429" "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "web-research-exa-crawl4ai SKILL.md menciona reduza a carga" {
  run grep -c "Reduza a carga" "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "web-research-exa-crawl4ai SKILL.md menciona chamadas sequenciais" {
  run grep -c "sequenciais" "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "web-research-exa-crawl4ai SKILL.md tem secao Fallback" {
  run grep -c "## Fallback" "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}

@test "web-research-exa-crawl4ai SKILL.md menciona doc-extract" {
  run grep -c "doc-extract" "$REPO_ROOT/skills/web-research-exa-crawl4ai/SKILL.md"
  assert_success
  [[ "$output" -ge 1 ]]
}
