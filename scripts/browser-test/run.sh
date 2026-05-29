#!/usr/bin/env bash
# scripts/browser-test/run
# Executa um script Playwright .js gerado pelo agente e retorna JSON.
#
# Uso: scripts/browser-test/run /tmp/browser-test-abc123.js
#
# Comportamento:
# 1. Valida que o arquivo existe e eh .js
# 2. Executa node <script> (no WSL se necessario)
# 3. Coleta stdout (JSON com resultado + screenshots)
# 4. Deleta o script (cleanup via trap)
# 5. Retorna JSON via stdout

set -euo pipefail

SCRIPT_PATH="${1:-}"

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
has_cmd() { command -v "$1" >/dev/null 2>&1; }

json_error() {
  local msg="$1"
  printf '{"ok":false,"error":"%s","screenshots":[],"console":[],"errors":["%s"],"duration_ms":0}\n' "$msg" "$msg"
  exit 1
}

is_wsl() {
  [ -f /proc/version ] && grep -qi microsoft /proc/version 2>/dev/null
}

# --------------------------------------------------------------------------
# Validacao
# --------------------------------------------------------------------------
if [ -z "$SCRIPT_PATH" ]; then
  json_error "Uso: scripts/browser-test/run <script.js>"
fi

if [ "--help" = "$SCRIPT_PATH" ] || [ "-h" = "$SCRIPT_PATH" ]; then
  cat <<'EOF'
scripts/browser-test/run

Executa um script Playwright .js e retorna resultado em JSON.

Uso:
  scripts/browser-test/run <path/to/script.js>

O script eh deletado apos execucao (cleanup automatico).
EOF
  exit 0
fi

# Se nao estamos no Linux, abortar
if [ "$(uname -s 2>/dev/null)" != "Linux" ]; then
  json_error "Execute este script dentro do WSL ou via wsl -e bash -c"
fi

# Validar extensao
case "$SCRIPT_PATH" in
  *.js) ;;
  *) json_error "Arquivo deve ter extensao .js: $SCRIPT_PATH" ;;
esac

# Validar existencia
if [ ! -f "$SCRIPT_PATH" ]; then
  json_error "Arquivo nao encontrado: $SCRIPT_PATH"
fi

# Verificar Node disponivel
if ! has_cmd node; then
  json_error "node nao encontrado no PATH. Execute install-playwright.sh primeiro"
fi

# Verificar Playwright disponivel
if ! has_cmd playwright && ! npm list -g @playwright/test --depth=0 >/dev/null 2>&1; then
  json_error "playwright nao instalado. Execute install-playwright.sh primeiro"
fi

# --------------------------------------------------------------------------
# Cleanup: deletar script ao final (sucesso ou falha)
# --------------------------------------------------------------------------
cleanup() {
  if [ -n "${SCRIPT_PATH:-}" ] && [ -f "$SCRIPT_PATH" ]; then
    rm -f "$SCRIPT_PATH"
  fi
}
trap cleanup EXIT

# --------------------------------------------------------------------------
# Execucao
# --------------------------------------------------------------------------
start_ms=$(date +%s%3N 2>/dev/null || date +%s000)

output=""
exit_code=0
output=$(node "$SCRIPT_PATH" 2>&1) || exit_code=$?

end_ms=$(date +%s%3N 2>/dev/null || date +%s000)
duration_ms=$(( end_ms - start_ms ))

# --------------------------------------------------------------------------
# Resultado
# --------------------------------------------------------------------------
if [ $exit_code -eq 0 ]; then
  # Verificar se output jah eh JSON valido
  if echo "$output" | head -1 | grep -q '^{'; then
    echo "$output"
  else
    # Wrap output generico em JSON
    escaped_output=$(printf '%s' "$output" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' ' ')
    printf '{"ok":true,"screenshots":[],"console":["%s"],"errors":[],"duration_ms":%d}\n' \
      "$escaped_output" "$duration_ms"
  fi
else
  escaped_output=$(printf '%s' "$output" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' ' ')
  printf '{"ok":false,"screenshots":[],"console":[],"errors":["%s"],"duration_ms":%d}\n' \
    "$escaped_output" "$duration_ms"
fi
