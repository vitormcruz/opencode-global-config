#!/usr/bin/env bash
# scripts/codebase-memory/install.sh
# Instala codebase-memory-mcp via npm e skills para OpenCode.
#
# Uso: ./scripts/codebase-memory/install.sh [--yes] [--check-only] [--help]

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
codebase-memory/install.sh

Instala codebase-memory-mcp via npm e skills em ~/.config/opencode/skills/.

Uso:
  ./scripts/codebase-memory/install.sh [--yes] [--check-only]

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
binary_installed=0
if command -v codebase-memory-mcp &>/dev/null; then
    print_success "codebase-memory-mcp ja instalado: $(codebase-memory-mcp --version 2>/dev/null | head -1 || echo 'versao desconhecida')"
    binary_installed=1
fi

if [ "$check_only" -eq 1 ]; then
    if [ "$binary_installed" -eq 0 ]; then
        print_warning "codebase-memory-mcp nao encontrado no PATH"
        print_info   "Execute sem --check-only para instalar"
    fi
    exit 0
fi

# --- Instalar binario (se necessario) ---
if [ "$binary_installed" -eq 0 ]; then

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
fi

# --- Instalar skills (OpenCode) ---
print_info "Instalando skills do codebase-memory..."
if codebase-memory-mcp install -y; then
    print_success "Skills codebase-memory instaladas para OpenCode"
else
    print_warning "codebase-memory-mcp install -y retornou erro"
fi

# Corrigir path absoluto que o binario escreve no opencode.json
# codebase-memory-mcp install grava o caminho completo do node_modules;
# queremos apenas o nome do binario (resolve via PATH).
# NOTA: resolvemos o symlink antes do sed -i porque sed quebra symlinks.
OPENCODE_JSON="$HOME/.config/opencode/opencode.json"
if [ -f "$OPENCODE_JSON" ]; then
    # Se for symlink, resolve o target para nao quebrar o link
    if [ -L "$OPENCODE_JSON" ]; then
        OPENCODE_TARGET=$(readlink -f "$OPENCODE_JSON")
    else
        OPENCODE_TARGET="$OPENCODE_JSON"
    fi
    # Remove entrada duplicada "codebase-memory-mcp" que o binario adiciona
    # (ja temos a entrada "codebase-memory" com o mesmo comando).
    if command -v jq &>/dev/null; then
        tmp_json="${OPENCODE_TARGET}.tmp.$$"
        jq --indent 4 'del(.mcp["codebase-memory-mcp"])' "$OPENCODE_TARGET" > "$tmp_json" && mv "$tmp_json" "$OPENCODE_TARGET"
        print_success "Entrada duplicada codebase-memory-mcp removida"
    fi
    # Corrige path absoluto para nome do binario (resolve via PATH)
    sed -i 's|"/home/[^"]*/\.local/lib/node_modules/codebase-memory-mcp/bin/codebase-memory-mcp"|"codebase-memory-mcp"|g' "$OPENCODE_TARGET"
    print_success "Path do codebase-memory-mcp corrigido para agnostico (PATH)"
fi
