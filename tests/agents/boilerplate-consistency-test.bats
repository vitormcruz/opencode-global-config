#!/usr/bin/env bats
# tests/agents/boilerplate-consistency-test.bats
#
# Valida que blocos de boilerplate compartilhados entre
# agentes do workflow dev permanecem idênticos.
#
# Grupos verificados:
#   Contrato Operacional: eng-software, front, qa, sec
#     (dba e rev têm variações legítimas e ficam de fora)
#   Evidências intro:     eng-software, front, qa, sec, dba, rev

setup() {
  load '../helpers/test_helper'
  AGENTS_DIR="${BATS_TEST_DIRNAME}/../../agents"
}

# ----------------------------------------------------------
# Helpers
# ----------------------------------------------------------

# Extrai de "## Contrato Operacional" até a próxima linha
# que seja exatamente "---" (separador de seção).
# Usa tr -d '\r' para normalizar CRLF → LF.
extract_contrato() {
  local file="$1"
  tr -d '\r' < "$file" | sed -n '/^## Contrato Operacional$/,/^---$/p'
}

# Extrai o texto introdutório de "## Evidências de Execução"
# até a linha antes do bloco de código (```markdown).
# Usa tr -d '\r' para normalizar CRLF → LF.
extract_evidencias_intro() {
  local file="$1"
  tr -d '\r' < "$file" | sed -n '/^## Evidências de Execução$/,/^```/{ /^```/d; p; }'
}

# ----------------------------------------------------------
# Contrato Operacional — eng, front, qa, sec
# ----------------------------------------------------------

@test "Contrato Operacional é idêntico entre eng-software, front, qa, sec" {
  local baseline
  baseline=$(extract_contrato "$AGENTS_DIR/eng-software.md")

  for agent in front qa sec; do
    local current
    current=$(extract_contrato "$AGENTS_DIR/${agent}.md")
    if [ "$current" != "$baseline" ]; then
      echo "DIVERGÊNCIA: ${agent}.md difere de eng-software.md (baseline)"
      diff <(echo "$baseline") <(echo "$current") || true
      fail "${agent}.md: Contrato Operacional divergiu do baseline (eng-software.md)"
    fi
  done
}

# ----------------------------------------------------------
# Evidências de Execução (intro) — eng, front, qa, sec, dba, rev
# ----------------------------------------------------------

@test "Evidências de Execução (intro) é idêntico entre eng, front, qa, sec, dba, rev" {
  local baseline
  baseline=$(extract_evidencias_intro "$AGENTS_DIR/eng-software.md")

  for agent in front qa sec dba rev; do
    local current
    current=$(extract_evidencias_intro "$AGENTS_DIR/${agent}.md")
    if [ "$current" != "$baseline" ]; then
      echo "DIVERGÊNCIA: ${agent}.md difere de eng-software.md (baseline)"
      diff <(echo "$baseline") <(echo "$current") || true
      fail "${agent}.md: Evidências intro divergiu do baseline (eng-software.md)"
    fi
  done
}
