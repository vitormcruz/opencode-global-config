#!/usr/bin/env bats
# tests/scripts/mapa-produto/scaffold-test.bats
#
# Valida o script de scaffold do /doc/README.md e
# tabela de harness, e a consistência do template
# entre fontes.

setup() {
  load '../../helpers/test_helper'
  SCRIPTS_DIR="${BATS_TEST_DIRNAME}/../../../scripts"
  AGENTS_DIR="${BATS_TEST_DIRNAME}/../../../agents"
  DOCS_DIR="${BATS_TEST_DIRNAME}/../../../docs"
  SCAFFOLD="${SCRIPTS_DIR}/mapa-produto/scaffold.sh"
}

# ----------------------------------------------------------
# Script de scaffold — existência e validação básica
# ----------------------------------------------------------

@test "scaffold.sh existe e é executável" {
  [ -f "$SCAFFOLD" ]
}

@test "scaffold.sh falha sem argumentos" {
  run bash "$SCAFFOLD"
  [ "$status" -eq 1 ]
}

@test "scaffold.sh falha com flag --doc sem valor" {
  run bash "$SCAFFOLD" --doc
  [ "$status" -eq 1 ]
}

@test "scaffold.sh falha com flag --harness sem valor" {
  run bash "$SCAFFOLD" --harness
  [ "$status" -eq 1 ]
}

@test "scaffold.sh falha com flag desconhecida" {
  run bash "$SCAFFOLD" --invalida
  [ "$status" -eq 1 ]
}

# ----------------------------------------------------------
# --doc: scaffold do /doc/README.md
# ----------------------------------------------------------

@test "--doc: cria seções do /doc/README.md em arquivo vazio" {
  common_setup
  local dest="$TEST_HOME/test-doc.md"
  touch "$dest"

  run bash "$SCAFFOLD" --doc "$dest"
  [ "$status" -eq 0 ]

  run grep "## Definição de Escopo" "$dest"
  [ "$status" -eq 0 ]

  run grep "## Elementos de Especificação" "$dest"
  [ "$status" -eq 0 ]

  run grep "### Regras de Documentação" "$dest"
  [ "$status" -eq 0 ]

  run grep "#### Regras Gerais" "$dest"
  [ "$status" -eq 0 ]

  run grep "## Estratégias de Indexação de Código" "$dest"
  [ "$status" -eq 0 ]

  common_teardown
}

@test "--doc: é idempotente — não duplica seções" {
  common_setup
  local dest="$TEST_HOME/test-doc.md"
  touch "$dest"

  bash "$SCAFFOLD" --doc "$dest"
  bash "$SCAFFOLD" --doc "$dest"

  local count
  count=$(grep -c "## Definição de Escopo" "$dest")
  [ "$count" -eq 1 ]

  common_teardown
}

@test "--doc: tabela de elementos contém defaults, não placeholder vazio" {
  common_setup
  local dest="$TEST_HOME/test-doc.md"

  run bash "$SCAFFOLD" --doc "$dest"
  [ "$status" -eq 0 ]

  run grep "(preencher)" "$dest"
  [ "$status" -ne 0 ]

  for elemento in "Critérios de Aceite + Requisitos" \
                   "Regras de Produto" "Modelo de Dados" \
                   "Threat Model" "Plano de Testes" \
                   "Identidade Visual" "ADR (Arquitetura)"; do
    run grep "| $elemento " "$dest"
    [ "$status" -eq 0 ]
  done

  run grep "Concordion" "$dest"
  [ "$status" -eq 0 ]

  run grep "DBML" "$dest"
  [ "$status" -eq 0 ]

  run grep "docs/specs/" "$dest"
  [ "$status" -eq 0 ]

  run grep "docs/modelo.dbml" "$dest"
  [ "$status" -eq 0 ]

  run grep "docs/threat-model.md" "$dest"
  [ "$status" -eq 0 ]

  run grep "plan/ui/" "$dest"
  [ "$status" -eq 0 ]

  run grep "docs/adr/" "$dest"
  [ "$status" -eq 0 ]

  common_teardown
}

@test "--doc: Regras Gerais presente com sugestões padrão" {
  common_setup
  local dest="$TEST_HOME/test-doc.md"

  run bash "$SCAFFOLD" --doc "$dest"
  [ "$status" -eq 0 ]

  run grep "#### Regras Gerais" "$dest"
  [ "$status" -eq 0 ]

  run grep "Documentação complementa o código" "$dest"
  [ "$status" -eq 0 ]

  run grep "Doc derivável do código não se armazena" "$dest"
  [ "$status" -eq 0 ]

  run grep "Doc desatualizada é pior que ausência" "$dest"
  [ "$status" -eq 0 ]

  common_teardown
}

@test "--doc: regras por elemento presentes com sugestões padrão" {
  common_setup
  local dest="$TEST_HOME/test-doc.md"

  run bash "$SCAFFOLD" --doc "$dest"
  [ "$status" -eq 0 ]

  for sec in "Critérios de Aceite + Requisitos" \
              "Regras de Produto" "Modelo de Dados" \
              "Threat Model" "Plano de Testes" \
              "Identidade Visual" "ADR (Arquitetura)"; do
    run grep "#### $sec" "$dest"
    [ "$status" -eq 0 ]
  done

  run grep "arquivo Concordion" "$dest"
  [ "$status" -eq 0 ]

  run grep "Seguir template ADR" "$dest"
  [ "$status" -eq 0 ]

  run grep "schema diff a cada alteração" "$dest"
  [ "$status" -eq 0 ]

  common_teardown
}

# ----------------------------------------------------------
# Compatibilidade retroativa (posicional = --doc)
# ----------------------------------------------------------

@test "posicional: chamada sem flag funciona como --doc" {
  common_setup
  local dest="$TEST_HOME/test-doc-legacy.md"

  run bash "$SCAFFOLD" "$dest"
  [ "$status" -eq 0 ]

  run grep "## Definição de Escopo" "$dest"
  [ "$status" -eq 0 ]

  run grep "### Regras de Documentação" "$dest"
  [ "$status" -eq 0 ]

  common_teardown
}

@test "posicional: é idempotente" {
  common_setup
  local dest="$TEST_HOME/test-doc-legacy.md"

  bash "$SCAFFOLD" "$dest"
  bash "$SCAFFOLD" "$dest"

  local count
  count=$(grep -c "## Definição de Escopo" "$dest")
  [ "$count" -eq 1 ]

  common_teardown
}

# ----------------------------------------------------------
# --harness: scaffold da tabela de harness
# ----------------------------------------------------------

@test "--harness: cria tabela de harness no AGENTS.md" {
  common_setup
  local dest="$TEST_HOME/AGENTS.md"
  touch "$dest"

  run bash "$SCAFFOLD" --harness "$dest"
  [ "$status" -eq 0 ]

  run grep "## Harness por Agente" "$dest"
  [ "$status" -eq 0 ]

  common_teardown
}

@test "--harness: lista todos os agentes obrigatórios" {
  common_setup
  local dest="$TEST_HOME/AGENTS.md"

  run bash "$SCAFFOLD" --harness "$dest"
  [ "$status" -eq 0 ]

  for agente in eng-software dba sec qa front rev \
                val-harness curador-produto; do
    run grep "| $agente " "$dest"
    [ "$status" -eq 0 ]
  done

  common_teardown
}

@test "--harness: agentes não-executores têm (sem harness)" {
  common_setup
  local dest="$TEST_HOME/AGENTS.md"

  run bash "$SCAFFOLD" --harness "$dest"
  [ "$status" -eq 0 ]

  for agente in rev val-harness curador-produto; do
    run grep "| $agente | (sem harness) | SEM HARNESS A PEDIDO DO HUMANO" "$dest"
    [ "$status" -eq 0 ]
  done

  common_teardown
}

@test "--harness: agentes executores têm comandos padrão" {
  common_setup
  local dest="$TEST_HOME/AGENTS.md"

  run bash "$SCAFFOLD" --harness "$dest"
  [ "$status" -eq 0 ]

  run grep "| eng-software | harness/eng-software.sh | Testes, análise estática" "$dest"
  [ "$status" -eq 0 ]

  run grep "| dba | harness/dba.sh | Validação de schema" "$dest"
  [ "$status" -eq 0 ]

  run grep "| sec | harness/sec.sh | OWASP checks, secrets" "$dest"
  [ "$status" -eq 0 ]

  run grep "| qa | harness/qa.sh | Cobertura, aceitação" "$dest"
  [ "$status" -eq 0 ]

  run grep "| front | harness/front.sh | Linting, a11y" "$dest"
  [ "$status" -eq 0 ]

  common_teardown
}

@test "--harness: é idempotente — não duplica tabela" {
  common_setup
  local dest="$TEST_HOME/AGENTS.md"
  touch "$dest"

  bash "$SCAFFOLD" --harness "$dest"
  bash "$SCAFFOLD" --harness "$dest"

  local count
  count=$(grep -c "## Harness por Agente" "$dest")
  [ "$count" -eq 1 ]

  common_teardown
}

@test "--harness: contém seção de especificação dos scripts" {
  common_setup
  local dest="$TEST_HOME/AGENTS.md"

  run bash "$SCAFFOLD" --harness "$dest"
  [ "$status" -eq 0 ]

  run grep "### Especificação dos Scripts de Harness" "$dest"
  [ "$status" -eq 0 ]

  common_teardown
}

@test "--harness: especificação descreve cada script executor" {
  common_setup
  local dest="$TEST_HOME/AGENTS.md"

  run bash "$SCAFFOLD" --harness "$dest"
  [ "$status" -eq 0 ]

  for sec in "harness/eng-software.sh" "harness/dba.sh" \
              "harness/sec.sh" "harness/qa.sh" \
              "harness/front.sh"; do
    run grep "#### $sec" "$dest"
    [ "$status" -eq 0 ]
  done

  common_teardown
}

@test "--harness: especificação descreve interface padronizada" {
  common_setup
  local dest="$TEST_HOME/AGENTS.md"

  run bash "$SCAFFOLD" --harness "$dest"
  [ "$status" -eq 0 ]

  run grep "sem argumentos" "$dest"
  [ "$status" -eq 0 ]

  run grep "saída JSON" "$dest"
  [ "$status" -eq 0 ]

  run grep "exit code" "$dest"
  [ "$status" -eq 0 ]

  common_teardown
}

# ----------------------------------------------------------
# --doc + --harness: ambos juntos
# ----------------------------------------------------------

@test "--doc + --harness: cria ambos os scaffolds" {
  common_setup
  local doc="$TEST_HOME/doc.md"
  local agents="$TEST_HOME/AGENTS.md"

  run bash "$SCAFFOLD" --doc "$doc" --harness "$agents"
  [ "$status" -eq 0 ]

  run grep "## Definição de Escopo" "$doc"
  [ "$status" -eq 0 ]

  run grep "## Harness por Agente" "$agents"
  [ "$status" -eq 0 ]

  common_teardown
}

# ----------------------------------------------------------
# Template do /doc/README.md — consistência entre fontes
# ----------------------------------------------------------

@test "workflow-curadoria.md contém as 3 seções do template" {
  local f="$DOCS_DIR/workflow-curadoria.md"
  run grep "Definição de Escopo" "$f"
  [ "$status" -eq 0 ]

  run grep "Elementos de Especificação" "$f"
  [ "$status" -eq 0 ]

  run grep "Estratégias de Indexação de Código" "$f"
  [ "$status" -eq 0 ]
}

@test "curador-produto-editor.md contém as 3 seções do template" {
  local f="$AGENTS_DIR/curador-produto-editor.md"
  run grep "Definição de Escopo" "$f"
  [ "$status" -eq 0 ]

  run grep "Elementos de Especificação" "$f"
  [ "$status" -eq 0 ]

  run grep "Estratégias de Indexação de Código" "$f"
  [ "$status" -eq 0 ]
}

@test "template do editor lista os mesmos elementos do workflow" {
  local workflow="$DOCS_DIR/workflow-curadoria.md"
  local editor="$AGENTS_DIR/curador-produto-editor.md"

  for elemento in "Modelo de Dados" "Threat Model" \
                   "Plano de Testes" \
                   "ADR (Arquitetura)"; do
    run grep "$elemento" "$workflow"
    [ "$status" -eq 0 ]
    run grep "$elemento" "$editor"
    [ "$status" -eq 0 ]
  done
}

@test "template do editor contém destino docs/specs/" {
  run grep "docs/specs/" "$AGENTS_DIR/curador-produto-editor.md"
  [ "$status" -eq 0 ]
}

@test "workflow-curadoria contém destino docs/specs/" {
  run grep "docs/specs/" "$DOCS_DIR/workflow-curadoria.md"
  [ "$status" -eq 0 ]
}

@test "tabela de harness no editor lista agentes obrigatórios" {
  local f="$AGENTS_DIR/curador-produto-editor.md"
  for agente in eng-software dba sec qa front rev \
                val-harness curador-produto; do
    run grep "| $agente " "$f"
    [ "$status" -eq 0 ]
  done
}

# ----------------------------------------------------------
# Consistência: scaffold vs workflow (harness interface)
# ----------------------------------------------------------

@test "workflow-curadoria não contém interface antiga de harness" {
  local f="$DOCS_DIR/workflow-curadoria.md"
  run grep "harness/<agente>/<fase>" "$f"
  [ "$status" -ne 0 ]
}

@test "workflow-curadoria descreve interface JSON padronizada" {
  local f="$DOCS_DIR/workflow-curadoria.md"
  run grep '"status"' "$f"
  [ "$status" -eq 0 ]
  run grep '"findings"' "$f"
  [ "$status" -eq 0 ]
}
