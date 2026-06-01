#!/usr/bin/env bash
# scripts/doctree/install.sh
# Instala bun via npm e verifica doctree-mcp.
#
# Uso: ./scripts/doctree/install.sh [--yes] [--check-only] [--help]

set -euo pipefail

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
doctree/install.sh

Instala bun (necessario para bunx doctree-mcp) via npm.

Uso:
  ./scripts/doctree/install.sh [--yes] [--check-only]

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

export PATH="$HOME/.bun/bin:$PATH"

bun_ok=0
doctree_ok=0

command -v bun &>/dev/null && bun_ok=1
if [ "$bun_ok" -eq 1 ] && bunx doctree-mcp --help &>/dev/null 2>&1; then
    doctree_ok=1
fi

if [ "$bun_ok" -eq 1 ] && [ "$doctree_ok" -eq 1 ]; then
    print_success "doctree-mcp disponivel (bun $(bun --version 2>/dev/null | head -1))"
    exit 0
fi

if [ "$check_only" -eq 1 ]; then
    if [ "$bun_ok" -eq 0 ]; then
        print_warning "bun nao encontrado"
    fi
    if [ "$doctree_ok" -eq 0 ]; then
        print_warning "doctree-mcp nao disponivel"
    fi
    print_info "Execute sem --check-only para instalar"
    exit 0
fi

# --- Instalar bun via npm ---
if [ "$bun_ok" -eq 0 ]; then
    if ! command -v npm &>/dev/null; then
        print_error "npm nao encontrado. Instale Node.js primeiro."
        exit 1
    fi

    # Garantir prefixo de usuario para evitar necessidade de sudo
    npm config set prefix "$HOME/.local" 2>/dev/null || true
    export PATH="$HOME/.local/bin:$PATH"

    if [ "$assume_yes" -ne 1 ]; then
        printf '  Instalar bun via npm agora? [y/N] '
        read -r ans || true
        case "$ans" in y|Y|yes|YES) ;; *) print_info "Abortado pelo usuario"; exit 0 ;; esac
    fi

    print_info "Instalando bun via npm..."
    if npm install -g bun; then
        export PATH="$HOME/.bun/bin:$PATH"
        if command -v bun &>/dev/null; then
            print_success "bun instalado: $(bun --version 2>/dev/null | head -1)"
            bun_ok=1
        else
            print_warning "bun instalado mas nao encontrado no PATH"
            print_info   "Execute: export PATH=\"\$HOME/.bun/bin:\$PATH\""
        fi
    else
        print_error "Falha ao instalar bun"
        print_info   "Verifique npm e conectividade"
        exit 1
    fi
fi

# --- Verificar doctree-mcp ---
if [ "$bun_ok" -eq 1 ]; then
    print_info "Verificando doctree-mcp..."
    if bunx doctree-mcp --help &>/dev/null 2>&1; then
        print_success "doctree-mcp disponivel e funcional"
    else
        print_warning "doctree-mcp nao respondeu — verifique manualmente: bunx doctree-mcp --help"
    fi
fi
