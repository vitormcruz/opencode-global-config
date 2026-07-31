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
CRAWL4AI_IMAGE="crawl4ai-sanitized:latest"
CRAWL4AI_PORT="11235"
CRAWL4AI_TOKEN="${CRAWL4AI_API_TOKEN:-opencode-local-crawl4ai}"

crawl4ai-configured() {
    docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$CRAWL4AI_NAME" 2>/dev/null \
        | grep -Fxq "CRAWL4AI_API_TOKEN=${CRAWL4AI_TOKEN}"
}

crawl4ai-wait() {
    local attempt
    for attempt in {1..30}; do
        if curl -sf --max-time 2 --connect-timeout 2 \
            -H "Authorization: Bearer ${CRAWL4AI_TOKEN}" \
            "http://127.0.0.1:${CRAWL4AI_PORT}/health" >/dev/null; then
            return 0
        fi
        sleep 1
    done
    echo "Crawl4AI não respondeu em http://127.0.0.1:${CRAWL4AI_PORT}" >&2
    return 1
}

crawl4ai-start() {
    if docker ps --format '{{.Names}}' | grep -q "^${CRAWL4AI_NAME}$"; then
        if crawl4ai-configured; then
            echo "Container $CRAWL4AI_NAME já está em execução"
        else
            echo "Container $CRAWL4AI_NAME usa configuração antiga; recriando..."
            docker rm -f "$CRAWL4AI_NAME" >/dev/null
        fi
    fi

    if ! docker ps --format '{{.Names}}' | grep -q "^${CRAWL4AI_NAME}$"; then
        echo "Iniciando container Crawl4AI MCP..."
        docker rm -f "$CRAWL4AI_NAME" 2>/dev/null || true
        docker run -d --name "$CRAWL4AI_NAME" \
            -p "${CRAWL4AI_PORT}:${CRAWL4AI_PORT}" \
            -e "CRAWL4AI_API_TOKEN=${CRAWL4AI_TOKEN}" \
            "$CRAWL4AI_IMAGE"
        echo "Container Crawl4AI MCP iniciado na porta $CRAWL4AI_PORT"
    fi

    if ! crawl4ai-wait; then
        docker logs --tail 20 "$CRAWL4AI_NAME" >&2 || true
        return 1
    fi
    echo "Crawl4AI MCP disponível em http://127.0.0.1:${CRAWL4AI_PORT}"
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
