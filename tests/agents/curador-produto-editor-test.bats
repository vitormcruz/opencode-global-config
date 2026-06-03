#!/usr/bin/env bats
# tests/agents/curador-produto-editor-test.bats
#
# Valida a estrutura do agente curador-produto-editor.

setup() {
  load '../helpers/test_helper'
  AGENTS_DIR="${BATS_TEST_DIRNAME}/../../agents"
}

# ----------------------------------------------------------
# Estrutura do agente
# ----------------------------------------------------------

@test "curador-produto-editor.md existe" {
  [ -f "$AGENTS_DIR/curador-produto-editor.md" ]
}

@test "curador-produto-editor.md tem frontmatter com description" {
  run grep -c "^description:" "$AGENTS_DIR/curador-produto-editor.md"
  [ "$output" -ge 1 ]
}

@test "curador-produto-editor.md não referencia validação de requisitos" {
  run grep -i "validar requisitos" "$AGENTS_DIR/curador-produto-editor.md"
  [ "$status" -ne 0 ]
}

@test "curador-produto-editor.md contém template do /doc/README.md" {
  run grep "Elementos de Especificação" "$AGENTS_DIR/curador-produto-editor.md"
  [ "$status" -eq 0 ]
}

@test "curador-produto-editor.md contém interface de harness JSON" {
  run grep '"status"' "$AGENTS_DIR/curador-produto-editor.md"
  [ "$status" -eq 0 ]
}

@test "curador-produto-editor.md tem seção de Limites" {
  run grep "^## Limites" "$AGENTS_DIR/curador-produto-editor.md"
  [ "$status" -eq 0 ]
}

@test "curador-produto-editor.md contém Definição de Escopo" {
  run grep "Definição de Escopo" "$AGENTS_DIR/curador-produto-editor.md"
  [ "$status" -eq 0 ]
}

@test "curador-produto-editor.md contém Estratégias de Indexação" {
  run grep "Estratégias de Indexação" "$AGENTS_DIR/curador-produto-editor.md"
  [ "$status" -eq 0 ]
}

# ----------------------------------------------------------
# Consistência curador-produto
# ----------------------------------------------------------

@test "curador-produto.md não contém 'Validar requisitos'" {
  run grep -i "Validar requisitos" "$AGENTS_DIR/curador-produto.md"
  [ "$status" -ne 0 ]
}

@test "curador-produto.md referencia curador-produto-editor" {
  run grep "curador-produto-editor" "$AGENTS_DIR/curador-produto.md"
  [ "$status" -eq 0 ]
}

@test "curador-produto.md não contém 'Mapa do Produto'" {
  run grep "Mapa do Produto" "$AGENTS_DIR/curador-produto.md"
  [ "$status" -ne 0 ]
}
