#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# Script de Instalação: Crawl4AI MCP para OpenCode
# 
# Este script configura automaticamente:
# - Docker + Container Crawl4AI
# - Script de start/stop/status
# - Configuração OpenCode (opencode.json)
# - Instruções AGENTS.md
# - Auto-inicialização no WSL (.bashrc)
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para print com cores
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ═══════════════════════════════════════════════════════════════════════════
# 1. Verificar Docker instalado
# ═══════════════════════════════════════════════════════════════════════════
print_info "Verificando Docker..."

if ! command -v docker &> /dev/null; then
    print_error "Docker não está instalado. Instale o Docker primeiro."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker não está em execução. Inicie o Docker primeiro."
    exit 1
fi

print_success "Docker está instalado e em execução"

# ═══════════════════════════════════════════════════════════════════════════
# 2. Baixar imagem Crawl4AI
# ═══════════════════════════════════════════════════════════════════════════
print_info "Baixando imagem Crawl4AI..."

if docker pull unclecode/crawl4ai:latest; then
    print_success "Imagem Crawl4AI baixada"
else
    print_error "Falha ao baixar imagem Crawl4AI"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════
# 3. Criar diretório de configuração
# ═══════════════════════════════════════════════════════════════════════════
print_info "Criando diretório de configuração..."

CONFIG_DIR="$HOME/.config/opencode"
mkdir -p "$CONFIG_DIR"
print_success "Diretório criado: $CONFIG_DIR"

# ═══════════════════════════════════════════════════════════════════════════
# 4. Criar script start-crawl4ai.sh
# ═══════════════════════════════════════════════════════════════════════════
print_info "Criando script de start/stop/status..."

cat > "$CONFIG_DIR/start-crawl4ai.sh" << 'SCRIPT_EOF'
#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# Script de Controle: Crawl4AI MCP
# 
# Usage:
#   source ~/.config/opencode/scripts/crawl4ai/start-crawl4ai.sh   # Carrega funções
#   crawl4ai-start     # Inicia o container
#   crawl4ai-stop      # Para o container
#   crawl4ai-restart   # Reinicia o container
#   crawl4ai-status   # Mostra status
# ═══════════════════════════════════════════════════════════════════════════

CRAWL4AI_NAME="crawl4ai-mcp"
CRAWL4AI_IMAGE="unclecode/crawl4ai:latest"
CRAWL4AI_PORT="11235"

crawl4ai-start() {
    if docker ps --format '{{.Names}}' | grep -q "^${CRAWL4AI_NAME}$"; then
        echo "Container $CRAWL4AI_NAME já está em execução"
    else
        echo "Iniciando container Crawl4AI MCP..."
        docker rm -f "$CRAWL4AI_NAME" 2>/dev/null || true
        docker run -d --name "$CRAWL4AI_NAME" -p "${CRAWL4AI_PORT}:${CRAWL4AI_PORT}" "$CRAWL4AI_IMAGE"
        echo "Container Crawl4AI MCP iniciado na porta $CRAWL4AI_PORT"
    fi
}

crawl4ai-stop() {
    if docker ps --format '{{.Names}}' | grep -q "^${CRAWL4AI_NAME}$"; then
        echo "Parando container Crawl4AI MCP..."
        docker stop "$CRAWL4AI_NAME" && docker rm "$CRAWL4AI_NAME"
        echo "Container Crawl4AI MCP parado e removido"
    else
        echo "Container Crawl4AI MCP não está em execução"
    fi
}

crawl4ai-restart() {
    crawl4ai-stop
    crawl4ai-start
}

crawl4ai-status() {
    if docker ps --format '{{.Names}}' | grep -q "^${CRAWL4AI_NAME}$"; then
        echo "Container Crawl4AI MCP está em execução"
        docker ps --filter "name=$CRAWL4AI_NAME" --format "  Status: {{.Status}}\n  Porta: {{.Ports}}"
    else
        echo "Container Crawl4AI MCP NÃO está em execução"
    fi
}

# Auto-iniciar ao carregar o script
crawl4ai-start
SCRIPT_EOF

chmod +x "$CONFIG_DIR/scripts/crawl4ai/start-crawl4ai.sh"
print_success "Script criado: $CONFIG_DIR/scripts/crawl4ai/start-crawl4ai.sh"

# ═══════════════════════════════════════════════════════════════════════════
# 5. Criar opencode.json
# ═══════════════════════════════════════════════════════════════════════════
print_info "Criando opencode.json..."

cat > "$CONFIG_DIR/opencode.json" << 'CONFIG_EOF'
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [],
  "instructions": ["~/.config/opencode/AGENTS.md"],
  "mcp": {
    "crawl4ai": {
      "type": "remote",
      "url": "http://localhost:11235/mcp/sse",
      "enabled": true
    }
  }
}
CONFIG_EOF

print_success "opencode.json criado"

# ═══════════════════════════════════════════════════════════════════════════
# 6. Criar AGENTS.md
# ═══════════════════════════════════════════════════════════════════════════
print_info "Criando AGENTS.md..."

cat > "$CONFIG_DIR/AGENTS.md" << 'AGENTS_EOF'
# Instruções Globais - Pesquisa Web

## REGRA PRINCIPAL: Sempre use MCP Crawl4AI para pesquisas na web

Quando o usuário pedir para fazer uma pesquisa, busca, ou obter informações da internet (ex: "pesquise sobre X", "busque informações de Y", "qual o preço de Z", "notícias sobre W", "melhores produtos de 2025/2026"), você **DEVE**:

1. **Usar APENAS o MCP Crawl4AI** - Nunca usar websearch, curl, ou outras ferramentas de busca
2. **Ferramentas disponíveis do Crawl4AI:**
   - `crawl4ai_md` - Extrai conteúdo de páginas web em formato markdown (MAIS IMPORTENTE)
   - `crawl4ai_html` - Retorna HTML processado da página
   - `crawl4ai_screenshot` - Captura screenshot PNG da página
   - `crawl4ai_pdf` - Gera PDF da página
   - `crawl4ai_crawl` - Crawl de múltiplas URLs retornando JSON
   - `crawl4ai_execute_js` - Executa JavaScript na página

## Exemplos de como FAZER

| Prompt do usuário | O que fazer |
|-----------------|-------------|
| "Pesquise as melhores canetas 3D de 2025" | Usar `crawl4ai_md` para buscar a página |
| "Qual o preço do 3Doodler?" | Usar `crawl4ai_md` no site oficial |
| "Busque notícias sobre IA" | Usar `crawl4ai_md` em sites de notícias |
| "Qual o preço médio de um notebook?" | Usar `crawl4ai_md` em sites de preços |

## Exemplos de como NÃO FAZER

- **NÃO** use `websearch` - Esta ferramenta está DESATIVADA para pesquisas
- **NÃO** use `curl` ou `bash` para buscar páginas web
- **NÃO** responda com conhecimento do modelo quando o usuário pedir pesquisa

## Quando perguntar ao usuário

**NÃO** pergunte se o usuário quer usar pesquisa web - simplesmente USE o MCP.

A única exceção é se você não tiver certeza se o usuário quer uma pesquisa ou não - neste caso, pode perguntar uma vez, mas depois use sempre o MCP.

## Como usar o Crawl4AI

Para buscar informações sobre um produto, primeiro encontre o site relevante e use `crawl4ai_md` com a URL.

Exemplo de fluxo:
1. Identificar URL relevante (ex: site oficial do produto)
2. Usar `crawl4ai_md` com a URL
3. Analisar o conteúdo retornado em markdown
4. Responder com as informações obtidas
AGENTS_EOF

print_success "AGENTS.md criado"

# ═══════════════════════════════════════════════════════════════════════════
# 7. Atualizar .bashrc
# ═══════════════════════════════════════════════════════════════════════════
print_info "Atualizando .bashrc..."

BASHRC="$HOME/.bashrc"
MARKER_START="# Crawl4AI MCP - INICIO"
MARKER_END="# Crawl4AI MCP - FIM"

# Verificar se já existe configuração
if grep -q "$MARKER_START" "$BASHRC" 2>/dev/null; then
    print_warning "Configuração Crawl4AI já existe no .bashrc, removendo..."
    # Remover configuração existente
    sed -i "/$MARKER_START/,/$MARKER_END/d" "$BASHRC"
fi

# Adicionar nova configuração
cat >> "$BASHRC" << BASHRC_EOF

$MARKER_START
# Auto-iniciar Crawl4AI MCP
if [ -f ~/.config/opencode/scripts/crawl4ai/start-crawl4ai.sh ]; then
    source ~/.config/opencode/scripts/crawl4ai/start-crawl4ai.sh
fi
$MARKER_END
BASHRC_EOF

print_success ".bashrc atualizado"

# ═══════════════════════════════════════════════════════════════════════════
# 8. Testar inicialização
# ═══════════════════════════════════════════════════════════════════════════
print_info "Testando inicialização..."

# Carregar script e iniciar
source "$CONFIG_DIR/scripts/crawl4ai/start-crawl4ai.sh"

# Verificar status
if docker ps --format '{{.Names}}' | grep -q "^${CRAWL4AI_NAME}$"; then
    print_success "Container Crawl4AI MCP está em execução na porta $CRAWL4AI_PORT"
else
    print_warning "Container pode não ter iniciado corretamente"
fi

# ═══════════════════════════════════════════════════════════════════════════
# FIM
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════════════════════"
print_success "Instalação concluída com sucesso!"
echo "══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Arquivos criados:"
echo "  - $CONFIG_DIR/scripts/crawl4ai/start-crawl4ai.sh"
echo "  - $CONFIG_DIR/scripts/crawl4ai/install-crawl4ai-mcp.sh"
echo "  - $CONFIG_DIR/opencode.json"
echo "  - $CONFIG_DIR/AGENTS.md"
echo ""
echo "O container Crawl4AI MCP será iniciado automaticamente ao abrir o terminal."
echo ""
echo "Comandos disponíveis (após abrir novo terminal):"
echo "  source ~/.config/opencode/scripts/crawl4ai/start-crawl4ai.sh"
echo "  crawl4ai-start    # Iniciar"
echo "  crawl4ai-stop     # Parar"
echo "  crawl4ai-restart  # Reiniciar"
echo "  crawl4ai-status   # Ver status"
echo ""
