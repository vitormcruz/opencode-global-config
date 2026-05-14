#!/usr/bin/env bats
# tests/scripts/mapa-produto/scaffold-test.bats
#
# Valida o script de scaffold do Mapa do Produto e a
# consistência do template entre fontes.

setup() {
  load '../../helpers/test_helper'
  SCRIPTS_DIR="${BATS_TEST_DIRNAME}/../../../scripts"
  AGENTS_DIR="${BATS_TEST_DIRNAME}/../../../agents"
  DOCS_DIR="${BATS_TEST_DIRNAME}/../../../docs"
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
# Template do Mapa — consistência entre fontes
# ----------------------------------------------------------

@test "workflow-curadoria.md contém as 3 seções do template" {
  local f="$DOCS_DIR/workflow-curadoria.md"
  run grep "Elementos de Especificação" "$f"
  [ "$status" -eq 0 ]

  run grep "Regras de Documentação" "$f"
  [ "$status" -eq 0 ]

  run grep "Harness por Agente" "$f"
  [ "$status" -eq 0 ]
}

@test "editor-mapa-produto.md contém as 3 seções do template" {
  local f="$AGENTS_DIR/editor-mapa-produto.md"
  run grep "Elementos de Especificação" "$f"
  [ "$status" -eq 0 ]

  run grep "Regras de Documentação" "$f"
  [ "$status" -eq 0 ]

  run grep "Harness por Agente" "$f"
  [ "$status" -eq 0 ]
}

@test "template do editor lista os mesmos elementos do workflow" {
  local workflow="$DOCS_DIR/workflow-curadoria.md"
  local editor="$AGENTS_DIR/editor-mapa-produto.md"

  # Elementos obrigatórios do template default
  for elemento in "Modelo de Dados" "Threat Model" \
                   "Plano de Testes" "Code as Doc" \
                   "ADR (Arquitetura)"; do
    run grep "$elemento" "$workflow"
    [ "$status" -eq 0 ]
    run grep "$elemento" "$editor"
    [ "$status" -eq 0 ]
  done
}

@test "template do editor contém destino docs/specs/" {
  run grep "docs/specs/" "$AGENTS_DIR/editor-mapa-produto.md"
  [ "$status" -eq 0 ]
}

@test "workflow-curadoria contém destino docs/specs/" {
  run grep "docs/specs/" "$DOCS_DIR/workflow-curadoria.md"
  [ "$status" -eq 0 ]
}

@test "tabela de harness lista agentes obrigatórios" {
  local f="$AGENTS_DIR/editor-mapa-produto.md"
  for agente in eng-software dba sec qa front rev \
                val-harness curador-produto; do
    run grep "| $agente" "$f"
    [ "$status" -eq 0 ]
  done
}
