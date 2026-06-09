#!/usr/bin/env bash
# scripts/doctree/install.sh
# Instala bun, verifica doctree-mcp e baixa skills para OpenCode.
# Nao materializa MCP especifico por repositorio; isso pertence ao fluxo
# de indexacao por repo quando existir `.env-doctree`.
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

Instala bun (necessario para bunx doctree-mcp) e baixa skills do doctree
para ~/.config/opencode/skills/.

Importante:
  este script instala a ferramenta global do doctree, mas nao cria a entrada
  MCP especifica de um repositorio.
  Se existir `.env-doctree` na raiz do repo, isso indica configuracao
  especifica e o MCP dedicado deve ser materializado pelo fluxo de indexacao.

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
if [ "$bun_ok" -eq 1 ] && command -v bunx &>/dev/null; then
    if timeout 5s bunx doctree-mcp </dev/null >/dev/null 2>&1; then
        doctree_ok=1
    else
        rc=$?
        if [ "$rc" -eq 124 ]; then
            doctree_ok=1
        fi
    fi
fi

if [ "$bun_ok" -eq 1 ] && [ "$doctree_ok" -eq 1 ]; then
    print_success "doctree-mcp disponivel (bun $(bun --version 2>/dev/null | head -1))"
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
    if timeout 5s bunx doctree-mcp </dev/null >/dev/null 2>&1; then
        print_success "doctree-mcp disponivel e funcional"
    else
        rc=$?
        if [ "$rc" -eq 124 ]; then
            print_success "doctree-mcp inicializa corretamente (servidor MCP em execucao)"
        else
            print_warning "doctree-mcp nao respondeu — verifique manualmente: timeout 5s bunx doctree-mcp"
        fi
    fi
fi

# --- Instalar skills do doctree (OpenCode) ---
OPENDIR="$HOME/.config/opencode/skills"

print_info "Baixando skills do doctree..."
if ! command -v curl &>/dev/null; then
    print_error "curl nao encontrado — necessario para baixar skills do doctree"
    exit 1
fi

for skill in doc-read doc-write doc-lint; do
    mkdir -p "$OPENDIR/$skill"
    url="https://raw.githubusercontent.com/joesaby/doctree-mcp/main/.claude/skills/$skill/SKILL.md"
    if curl -fsSL "$url" -o "$OPENDIR/$skill/SKILL.md"; then
        print_success "Skill baixada: $skill"
    else
        print_warning "Falha ao baixar skill: $skill ($url)"
    fi
done
