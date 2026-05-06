#!/usr/bin/env bash
# scripts/browser-test/install-playwright.sh
# Instala Playwright (Node.js + @playwright/test + chromium) no WSL.
# Idempotente: se já instalado, reporta OK e sai.
#
# Uso: ./scripts/browser-test/install-playwright.sh [--yes] [--check-only]

set -euo pipefail

assume_yes=0
check_only=0

while [ $# -gt 0 ]; do
  case "$1" in
    --yes)        assume_yes=1 ;;
    --check-only) check_only=1 ;;
    --help|-h)
      cat <<'EOF'
install-playwright.sh

Instala Playwright no WSL para testes de browser.

Uso:
  ./scripts/browser-test/install-playwright.sh [--yes] [--check-only]

Opcoes:
  --yes         Instala sem pedir confirmacao
  --check-only  Apenas verifica status (nao instala)
  --help        Mostra esta ajuda
EOF
      exit 0
      ;;
    *) echo "Opcao desconhecida: $1" >&2; exit 2 ;;
  esac
  shift
done

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
has_cmd() { command -v "$1" >/dev/null 2>&1; }

confirm_action() {
  local msg="$1"
  if [ "$assume_yes" -eq 1 ]; then return 0; fi
  if ! [ -t 0 ] || ! [ -t 1 ]; then return 0; fi
  printf '%s [y/N] ' "$msg"
  read -r ans || true
  case "$ans" in y|Y|yes|YES) return 0 ;; esac
  return 1
}

# --------------------------------------------------------------------------
# Detectar Node.js
# --------------------------------------------------------------------------
check_node() {
  if has_cmd node; then
    local ver
    ver="$(node --version 2>/dev/null || echo "")"
    local major="${ver#v}"
    major="${major%%.*}"
    if [ "${major:-0}" -ge 18 ]; then
      return 0
    fi
  fi
  return 1
}

# --------------------------------------------------------------------------
# Instalar Node.js via nvm (user-space)
# --------------------------------------------------------------------------
install_node() {
  local nvm_dir="${NVM_DIR:-$HOME/.nvm}"

  if [ ! -s "$nvm_dir/nvm.sh" ]; then
    echo "  -> Instalando nvm..."
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
    export NVM_DIR="$nvm_dir"
  fi

  # shellcheck source=/dev/null
  . "$nvm_dir/nvm.sh"
  echo "  -> Instalando Node.js 22 via nvm..."
  nvm install 22
  nvm use 22
}

# --------------------------------------------------------------------------
# Verificar Playwright
# --------------------------------------------------------------------------
check_playwright() {
  # Inclui user-space no PATH para encontrar playwright instalado sem sudo
  export PATH="$HOME/.local/bin:$PATH"
  if has_cmd playwright; then
    return 0
  fi
  if npm list -g @playwright/test --prefix "$HOME/.local" --depth=0 >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

# --------------------------------------------------------------------------
# Instalar Playwright
# --------------------------------------------------------------------------
install_playwright() {
  local prefix="$HOME/.local"
  mkdir -p "$prefix/lib" "$prefix/bin"

  echo "  -> Instalando @playwright/test em $prefix (user-space)..."
  npm install -g @playwright/test --prefix "$prefix"

  # Garantir que $prefix/bin esta no PATH
  export PATH="$prefix/bin:$PATH"

  echo "  -> Baixando browser chromium (user-space)..."
  playwright install chromium

  # Dependencias de sistema do chromium precisam de sudo.
  # Nao executamos sudo automaticamente — exibimos o comando para o usuario.
  echo ""
  echo "  ATENCAO: para o chromium funcionar, instale as dependencias de"
  echo "  sistema com sudo (execute manualmente no WSL):"
  echo ""
  echo "    sudo playwright install-deps chromium"
  echo ""
}

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
echo "=== install-playwright.sh ==="
echo ""

# Status Node.js
if check_node; then
  echo "  OK       node $(node --version 2>/dev/null)"
  node_ok=1
else
  echo "  MISSING  node >= 18"
  node_ok=0
fi

# Status Playwright
if check_playwright; then
  echo "  OK       playwright $(npx playwright --version 2>/dev/null)"
  pw_ok=1
else
  echo "  MISSING  @playwright/test"
  pw_ok=0
fi

echo ""

# Se tudo OK, sair
if [ "$node_ok" -eq 1 ] && [ "$pw_ok" -eq 1 ]; then
  echo "Status: OK"
  exit 0
fi

# Se check-only, reportar missing e sair
if [ "$check_only" -eq 1 ]; then
  echo "Status: MISSING"
  exit 1
fi

# Instalar Node.js se necessario
if [ "$node_ok" -eq 0 ]; then
  if confirm_action "Instalar Node.js 22 via nvm?"; then
    install_node
  else
    echo "Node.js necessario. Abortando."
    exit 1
  fi
fi

# Instalar Playwright
if [ "$pw_ok" -eq 0 ]; then
  if confirm_action "Instalar @playwright/test + chromium?"; then
    install_playwright
    echo ""
    echo "Status: INSTALLED"
    exit 0
  else
    echo "Playwright nao instalado."
    exit 1
  fi
fi

echo "Status: OK"
