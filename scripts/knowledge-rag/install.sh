#!/usr/bin/env bash
# scripts/knowledge-rag/install.sh
# Instala knowledge-rag via pipx e configura o servidor MCP.
# Nao materializa MCP especifico por repositorio; isso pertence ao fluxo
# de indexacao por repo quando existir `.env-knowledge-rag`.
#
# Uso: ./scripts/knowledge-rag/install.sh [--yes] [--check-only] [--help]

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
knowledge-rag/install.sh

Instala knowledge-rag via pipx para uso como MCP de documentacao.
Substitui o doctree-mcp anterior.

Importante:
  este script instala a ferramenta global do knowledge-rag, mas nao cria a
  entrada MCP especifica de um repositorio.
  Se existir `.env-knowledge-rag` na raiz do repo, isso indica configuracao
  especifica e o MCP dedicado deve ser materializado pelo fluxo de indexacao.

Uso:
  ./scripts/knowledge-rag/install.sh [--yes] [--check-only]

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

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# Verificar Python 3.10+
# -----------------------------------------------------------------------------

PYTHON3_VERSION=""
check_python3_version() {
    if ! has_cmd python3; then return 1; fi
    PYTHON3_VERSION="$(python3 --version 2>/dev/null | awk '{print $2}')"
    local minor
    minor="$(echo "$PYTHON3_VERSION" | cut -d. -f2)"
    [ -n "$minor" ] && [ "$minor" -ge 10 ] 2>/dev/null
}

# -----------------------------------------------------------------------------
# Verificar pipx
# -----------------------------------------------------------------------------

ensure_pipx() {
    if has_cmd pipx; then
        print_success "pipx $(pipx --version 2>/dev/null | head -1)"
        return 0
    fi

    print_warning "pipx nao encontrado"
    
    # Tentar instalar via pip --user
    print_info "Tentando instalar pipx via pip..."
    if has_cmd pip3; then
        pip3 install --user pipx --quiet 2>/dev/null || true
    elif has_cmd pip; then
        pip install --user pipx --quiet 2>/dev/null || true
    fi

    # Recarregar PATH
    export PATH="$HOME/.local/bin:$PATH"
    
    if has_cmd pipx; then
        print_success "pipx instalado via pip --user"
        return 0
    fi

    print_error "pipx nao disponivel. Instale manualmente:"
    print_info "  sudo apt-get install -y pipx  (Ubuntu/Debian)"
    print_info "  brew install pipx              (macOS)"
    return 1
}

# -----------------------------------------------------------------------------
# Instalar knowledge-rag
# -----------------------------------------------------------------------------

install_knowledge_rag() {
    print_info "Instalando knowledge-rag via pipx..."
    pipx install knowledge-rag 2>&1 | while IFS= read -r line; do
        print_info "  $line"
    done
    pipx ensurepath 2>/dev/null || true
}

# -----------------------------------------------------------------------------
# Verificar instalacao do knowledge-rag
# -----------------------------------------------------------------------------

check_knowledge_rag() {
    if has_cmd knowledge-rag; then
        local version
        version="$(knowledge-rag --version 2>/dev/null | head -1 || echo 'desconhecida')"
        print_success "knowledge-rag ($version)"
        return 0
    fi
    return 1
}

# -----------------------------------------------------------------------------
# Criar symlink do wrapper
# -----------------------------------------------------------------------------

create_wrapper_symlink() {
    local wrapper="$repo_root/scripts/knowledge-rag/run.sh"
    local target="$HOME/.local/bin/opencode-knowledge-rag-run"
    
    if [ -L "$target" ] || [ -e "$target" ]; then
        rm -f "$target" 2>/dev/null || true
    fi
    
    if [ -f "$wrapper" ]; then
        mkdir -p "$(dirname "$target")"
        ln -s "$wrapper" "$target"
        print_success "Link simbolico criado: $target -> $wrapper"
    else
        print_warning "Wrapper nao encontrado em $wrapper"
    fi
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"

check_python3_version || {
    print_error "Python 3.10+ requerido (tem: ${PYTHON3_VERSION:-nenhum})"
    exit 1
}

print_info "Python $PYTHON3_VERSION detectado"

if [ "$check_only" -eq 1 ]; then
    print_info "Modo check-only: apenas verificando..."
    
    if check_knowledge_rag; then
        print_success "knowledge-rag disponivel"
        exit 0
    else
        print_error "knowledge-rag nao encontrado"
        exit 1
    fi
fi

# Verificar/instalar pipx
if ! ensure_pipx; then
    print_error "Nao foi possivel garantir pipx"
    exit 1
fi

# Verificar se ja esta instalado
if check_knowledge_rag; then
    print_success "knowledge-rag ja instalado"
    create_wrapper_symlink
    exit 0
fi

# Perguntar e instalar
if confirm_action "Instalar knowledge-rag via pipx agora?"; then
    install_knowledge_rag
    export PATH="$HOME/.local/bin:$PATH"
    
    if check_knowledge_rag; then
        print_success "knowledge-rag instalado com sucesso"
        create_wrapper_symlink
    else
        print_error "knowledge-rag instalado mas nao encontrado no PATH"
        print_info "Execute: export PATH=\"\$HOME/.local/bin:\$PATH\""
        exit 1
    fi
else
    print_warning "Instalacao cancelada"
    print_info "Para instalar depois: pipx install knowledge-rag"
    exit 0
fi
