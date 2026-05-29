#!/usr/bin/env bash
# scripts/codebase-memory/install
# Instala codebase-memory-mcp via npm (gerenciador de pacotes).
#
# Uso: ./scripts/codebase-memory/install [--yes] [--check-only] [--help]

set -euo pipefail

INSTALL_DIR="${HOME}/.local/bin"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

assume_yes=0
check_only=0

while [ $# -gt 0 ]; do
    case "$1" in
        --yes)   assume_yes=1 ;;
        --check-only) check_only=1 ;;
        --help|-h)
            cat <<'EOF'
codebase-memory/install

Instala codebase-memory-mcp via npm.

Uso:
  ./scripts/codebase-memory/install [--yes] [--check-only]

Opcoes:
  --yes         Instala sem pedir confirmacao
  --check-only  Apenas verifica, nao instala
  --help        Mostra esta ajuda
EOF
            exit 0
            ;;
        *) print_error "Opcao desconhecida: $1"; exit 2 ;;
    esac
    shift
done

export PATH="$INSTALL_DIR:$PATH"

# --- Verificar se ja esta instalado ---
if command -v codebase-memory-mcp &>/dev/null; then
    print_success "codebase-memory-mcp ja instalado: $(codebase-memory-mcp --version 2>/dev/null | head -1 || echo 'versao desconhecida')"
    exit 0
fi

if [ "$check_only" -eq 1 ]; then
    print_warning "codebase-memory-mcp nao encontrado no PATH"
    print_info   "Execute sem --check-only para instalar"
    exit 0
fi

# --- Prerequisitos ---
if ! command -v npm &>/dev/null; then
    print_error "npm nao encontrado. Instale Node.js primeiro."
    exit 1
fi

# Garantir prefixo de usuario para evitar necessidade de sudo
npm config set prefix "$HOME/.local" 2>/dev/null || true
export PATH="$HOME/.local/bin:$PATH"

if [ "$assume_yes" -ne 1 ]; then
    printf '  Instalar codebase-memory-mcp agora? [y/N] '
    read -r ans || true
    case "$ans" in y|Y|yes|YES) ;; *) print_info "Abortado pelo usuario"; exit 0 ;; esac
fi

print_info "Instalando codebase-memory-mcp via npm..."
if npm install -g codebase-memory-mcp --ignore-scripts; then
    export PATH="$INSTALL_DIR:$PATH"
    if command -v codebase-memory-mcp &>/dev/null; then
        print_success "codebase-memory-mcp instalado: $(codebase-memory-mcp --version 2>/dev/null | head -1 || echo 'ok')"
    else
        print_warning "Instalado mas nao encontrado no PATH"
        print_info   "Execute: export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
else
    print_error "Falha ao instalar codebase-memory-mcp"
    print_info   "Verifique npm e conectividade"
    exit 1
fi
