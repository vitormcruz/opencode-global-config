#!/usr/bin/env bats
# tests/agents/smart-planner-test.bats
#
# Valida o conteudo de agents/smart-planner.md e
# a restricao comportamental no AGENTS.md.

setup() {
  load '../helpers/test_helper'
  AGENT="${BATS_TEST_DIRNAME}/../../agents/smart-planner.md"
  AGENTS_MD="${BATS_TEST_DIRNAME}/../../AGENTS.md"
}

# ----------------------------------------------------------
# Frontmatter
# ----------------------------------------------------------

@test "smart-planner: arquivo existe" {
  [ -f "$AGENT" ]
}

@test "smart-planner: frontmatter tem description" {
  run grep -q "^description:" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: frontmatter tem mode primary" {
  run grep -q "^mode: primary" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: frontmatter tem temperature" {
  run grep -q "^temperature:" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: frontmatter tem permission edit allow" {
  run grep -q "edit: allow" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: frontmatter tem permission bash allow" {
  run grep -q "bash: allow" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: frontmatter tem webfetch deny" {
  run grep -q "webfetch: deny" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: frontmatter tem task deny" {
  run grep -q '"\*": deny' "$AGENT"
  [ "$status" -eq 0 ]
}

# ----------------------------------------------------------
# Secoes obrigatorias
# ----------------------------------------------------------

@test "smart-planner: secao Modo de Operacao" {
  run grep -q "## Modo de Opera" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: secao Restricao Comportamental" {
  run grep -q "## Restri" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: secao Salvamento Incremental" {
  run grep -q "## Salvamento Incremental" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: secao Gate de Decisao e Commit" {
  run grep -q "## Gate de Decis" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: commit obrigatorio apos cada decisao" {
  run grep -q "Após CADA decisão aprovada" "$AGENT"
  [ "$status" -eq 0 ]
  run grep -q "SÓ ENTÃO faça a próxima pergunta" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: skeleton existe antes da primeira pergunta" {
  run grep -q "Antes da primeira pergunta" "$AGENT"
  [ "$status" -eq 0 ]
  run grep -q "skeleton" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: commit intermediario nao e opcional" {
  run grep -q "commit intermediário é obrigatório, não opcional" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: contra-proposta exige aprovacao explicita" {
  run grep -q "contra-proposta" "$AGENT"
  [ "$status" -eq 0 ]
  run grep -Fq "Posso registrar assim?" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: nao pula ramo obvio" {
  run grep -q "NUNCA pule um ramo independente" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: secao Stopping Conditions" {
  run grep -q "## Stopping Conditions" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: secao Handoff" {
  run grep -q "## Handoff" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: secao Limites" {
  run grep -q "## Limites" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: secao Protocolo de Replan" {
  run grep -q "## Protocolo de Replan" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: secao Revisao do Executor" {
  run grep -q "## Revis" "$AGENT"
  [ "$status" -eq 0 ]
}

# ----------------------------------------------------------
# Referencias a skills
# ----------------------------------------------------------

@test "smart-planner: referencia ao skill grill-me" {
  run grep -q "grill-me" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: referencia ao skill planning-and-task-breakdown" {
  run grep -q "planning-and-task-breakdown" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: referencia ao skill caveman" {
  run grep -q "caveman" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: referencia ao skill prompt-improver" {
  run grep -q "prompt-improver" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: decisoes distintas usam commits distintos" {
  run grep -q "Decisões diferentes" "$AGENT"
  [ "$status" -eq 0 ]
  run grep -q "commits diferentes" "$AGENT"
  [ "$status" -eq 0 ]
}

# ----------------------------------------------------------
# Conteudo chave
# ----------------------------------------------------------

@test "smart-planner: NUNCA edita codigo de aplicacao" {
  run grep -q "NUNCA.*edita" "$AGENT"
  [ "$status" -eq 0 ]
}

@test "smart-planner: PT-BR com acentuacao" {
  run grep -q "PT-BR" "$AGENT"
  [ "$status" -eq 0 ]
}

# ----------------------------------------------------------
# AGENTS.md — restricao comportamental
# ----------------------------------------------------------

@test "AGENTS.md: contem restricao do SmartPlanner" {
  run grep -qi "smart-planner.*nunca.*edita codigo\|SmartPlanner.*Restricao" "$AGENTS_MD"
  [ "$status" -eq 0 ]
}
