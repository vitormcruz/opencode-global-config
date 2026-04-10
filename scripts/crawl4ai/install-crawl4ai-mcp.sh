#!/bin/bash
# install-crawl4ai-mcp.sh
#
# Responsabilidade: configurar Docker + container Crawl4AI e registrar
# o auto-start no ~/.bashrc.
#
# O que este script FAZ:
#   1. Verifica Docker instalado e em execução
#   2. Pull da imagem unclecode/crawl4ai:latest
#   3. Build da imagem crawl4ai-sanitized:latest
#   4. Garante bloco de auto-start no ~/.bashrc (idempotente)
#   5. Inicia o container pela primeira vez
#
# O que este script NÃO FAZ:
#   - Não cria nem modifica arquivos em ~/.config/opencode/
#   - Não cria AGENTS.md global
#   - Não cria opencode.json
#   - Não cria scripts em ~/.config/opencode/scripts/
#
# A configuração do MCP (opencode.json) e os symlinks são gerenciados
# pelo script scripts/bootstrap_repo/opencode-link, que é o fonte de verdade
# para o setup global.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOCKER_DIR="$SCRIPT_DIR/docker"

BASHRC="${HOME}/.bashrc"
MARKER_START="# Crawl4AI MCP - INICIO"
MARKER_END="# Crawl4AI MCP - FIM"

# ═══════════════════════════════════════════════════════════════════════════
# 1. Verificar Docker
# ═══════════════════════════════════════════════════════════════════════════
print_info "Verificando Docker..."

if ! command -v docker &>/dev/null; then
    print_error "Docker não está instalado. Instale o Docker primeiro."
    exit 1
fi

if ! docker info &>/dev/null; then
    print_error "Docker não está em execução. Inicie o Docker primeiro."
    exit 1
fi

print_success "Docker está instalado e em execução"

# ═══════════════════════════════════════════════════════════════════════════
# 2. Pull da imagem Crawl4AI
# ═══════════════════════════════════════════════════════════════════════════
print_info "Baixando imagem Crawl4AI..."

if docker pull unclecode/crawl4ai:latest; then
    print_success "Imagem Crawl4AI baixada"
else
    print_error "Falha ao baixar imagem Crawl4AI"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════
# 3. Build da imagem sanitizada
# ═══════════════════════════════════════════════════════════════════════════
print_info "Construindo imagem crawl4ai-sanitized..."

if [ ! -d "$DOCKER_DIR" ] || [ ! -f "$DOCKER_DIR/Dockerfile" ]; then
    print_error "Diretório docker não encontrado: $DOCKER_DIR"
    exit 1
fi

if docker build -t crawl4ai-sanitized:latest "$DOCKER_DIR"; then
    print_success "Imagem crawl4ai-sanitized construída"
else
    print_error "Falha ao construir imagem sanitizada"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════
# 4. Bloco de auto-start no ~/.bashrc (idempotente via markers)
# ═══════════════════════════════════════════════════════════════════════════
print_info "Configurando auto-start no .bashrc..."

# Remove bloco anterior se existir (idempotência)
if grep -q "$MARKER_START" "$BASHRC" 2>/dev/null; then
    print_warning "Bloco Crawl4AI já existe no .bashrc — atualizando..."
    sed -i "/$MARKER_START/,/$MARKER_END/d" "$BASHRC"
fi

cat >> "$BASHRC" << BASHRC_EOF

$MARKER_START
# Auto-iniciar Crawl4AI MCP ao abrir terminal
_crawl4ai_autostart() {
    local name="crawl4ai-mcp"
    local image="crawl4ai-sanitized:latest"
    local port="11235"
    if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
        if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^\${name}\$"; then
            docker rm -f "\$name" 2>/dev/null || true
            docker run -d --name "\$name" -p "\${port}:\${port}" "\$image" \
                >/dev/null 2>&1 || true
        fi
    fi
}
_crawl4ai_autostart
$MARKER_END
BASHRC_EOF

print_success ".bashrc atualizado"

# ═══════════════════════════════════════════════════════════════════════════
# 5. Iniciar container
# ═══════════════════════════════════════════════════════════════════════════
print_info "Iniciando container Crawl4AI MCP..."

CRAWL4AI_NAME="crawl4ai-mcp"
CRAWL4AI_PORT="11235"

docker rm -f "$CRAWL4AI_NAME" 2>/dev/null || true
docker run -d --name "$CRAWL4AI_NAME" -p "${CRAWL4AI_PORT}:${CRAWL4AI_PORT}" \
    crawl4ai-sanitized:latest

if docker ps --format '{{.Names}}' | grep -q "^${CRAWL4AI_NAME}$"; then
    print_success "Container Crawl4AI MCP em execução na porta $CRAWL4AI_PORT"
else
    print_warning "Container pode não ter iniciado corretamente"
fi

# ═══════════════════════════════════════════════════════════════════════════
echo ""
print_success "Instalação concluída!"
echo ""
echo "Comandos úteis:"
echo "  docker ps -f name=crawl4ai-mcp     # Ver status"
echo "  docker stop crawl4ai-mcp           # Parar"
echo "  docker start crawl4ai-mcp          # Reiniciar"
