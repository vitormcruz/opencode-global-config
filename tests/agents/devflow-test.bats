#!/usr/bin/env bats
# tests/agents/devflow-test.bats
#
# Valida o conteúdo de agents/devflow.md — mediação de comunicação.

setup() {
  DEVFLOW="${BATS_TEST_DIRNAME}/../../agents/devflow.md"
}

# ----------------------------------------------------------
# Seção de mediação
# ----------------------------------------------------------

@test "devflow: seção de mediação presente" {
  run grep -q "Função de mediação" "$DEVFLOW"
  [ "$status" -eq 0 ]
}

# ----------------------------------------------------------
# Grill-me sob demanda (Devflow usa internamente)
# ----------------------------------------------------------

@test "devflow: grill-me sob demanda na mediação" {
  run grep -q "grill-me" "$DEVFLOW"
  [ "$status" -eq 0 ]

  run grep -qi "avalia.*qualidade\|conforme a complexidade" "$DEVFLOW"
  [ "$status" -eq 0 ]
}

# ----------------------------------------------------------
# Contrato item 6
# ----------------------------------------------------------

@test "devflow: contrato tem item 6" {
  run grep -q "^6\." "$DEVFLOW"
  [ "$status" -eq 0 ]

  run grep -q "Não precisa concluir a tarefa" "$DEVFLOW"
  [ "$status" -eq 0 ]
}

# ----------------------------------------------------------
# Contrato não instrui agente a usar grill-me
# ----------------------------------------------------------

@test "devflow: contrato não menciona grill-me" {
  run bash -c "grep -A 20 'Contrato com agentes spawnados' '$DEVFLOW' | grep -q 'grill-me'"
  [ "$status" -ne 0 ]
}
