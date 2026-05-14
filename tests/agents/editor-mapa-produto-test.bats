#!/usr/bin/env bats
# tests/agents/editor-mapa-produto-test.bats
#
# Valida a estrutura do agente editor-mapa-produto e o
# script de scaffold.

setup() {
  load '../helpers/test_helper'
  AGENTS_DIR="${BATS_TEST_DIRNAME}/../../agents"
  SCRIPTS_DIR="${BATS_TEST_DIRNAME}/../../scripts"
}

# ----------------------------------------------------------
# Estrutura do agente
# ----------------------------------------------------------

@test "editor-mapa-produto.md existe" {
  [ -f "$AGENTS_DIR/editor-mapa-produto.md" ]
}

@test "editor-mapa-produto.md tem frontmatter com description" {
  run grep -c "^description:" "$AGENTS_DIR/editor-mapa-produto.md"
  [ "$output" -ge 1 ]
}

@test "editor-mapa-produto.md não referencia validação de requisitos" {
  run grep -i "validar requisitos" "$AGENTS_DIR/editor-mapa-produto.md"
  [ "$status" -ne 0 ]
}

@test "editor-mapa-produto.md contém template do Mapa" {
  run grep "Elementos de Especificação" "$AGENTS_DIR/editor-mapa-produto.md"
  [ "$status" -eq 0 ]
}

@test "editor-mapa-produto.md contém interface de harness JSON" {
  run grep '"status"' "$AGENTS_DIR/editor-mapa-produto.md"
  [ "$status" -eq 0 ]
}

@test "editor-mapa-produto.md tem seção de Limites" {
  run grep "^## Limites" "$AGENTS_DIR/editor-mapa-produto.md"
  [ "$status" -eq 0 ]
}

# ----------------------------------------------------------
# Script de scaffold
# ----------------------------------------------------------

@test "scaffold.sh existe e é executável" {
  [ -f "$SCRIPTS_DIR/mapa-produto/scaffold.sh" ]
}

@test "scaffold.sh cria seções do Mapa em arquivo vazio" {
  common_setup
  local dest="$TEST_HOME/test-agents.md"
  touch "$dest"

  run bash "$SCRIPTS_DIR/mapa-produto/scaffold.sh" "$dest"
  [ "$status" -eq 0 ]

  # Verifica seções criadas
  run grep "## Mapa do Produto" "$dest"
  [ "$status" -eq 0 ]

  run grep "### Elementos de Especificação" "$dest"
  [ "$status" -eq 0 ]

  run grep "### Regras de Documentação" "$dest"
  [ "$status" -eq 0 ]

  run grep "### Harness por Agente" "$dest"
  [ "$status" -eq 0 ]

  common_teardown
}

@test "scaffold.sh é idempotente — não duplica seções" {
  common_setup
  local dest="$TEST_HOME/test-agents.md"
  touch "$dest"

  bash "$SCRIPTS_DIR/mapa-produto/scaffold.sh" "$dest"
  bash "$SCRIPTS_DIR/mapa-produto/scaffold.sh" "$dest"

  local count
  count=$(grep -c "## Mapa do Produto" "$dest")
  [ "$count" -eq 1 ]

  common_teardown
}

@test "scaffold.sh falha sem argumento" {
  run bash "$SCRIPTS_DIR/mapa-produto/scaffold.sh"
  [ "$status" -eq 1 ]
}

# ----------------------------------------------------------
# Consistência curador-produto
# ----------------------------------------------------------

@test "curador-produto.md não contém 'Validar requisitos'" {
  run grep -i "Validar requisitos" "$AGENTS_DIR/curador-produto.md"
  [ "$status" -ne 0 ]
}

@test "curador-produto.md referencia editor-mapa-produto" {
  run grep "editor-mapa-produto" "$AGENTS_DIR/curador-produto.md"
  [ "$status" -eq 0 ]
}

@test "curador-produto.md contém 'Não altera Mapa/harness'" {
  run grep -i "Não altera Mapa" "$AGENTS_DIR/curador-produto.md"
  [ "$status" -eq 0 ]
}
